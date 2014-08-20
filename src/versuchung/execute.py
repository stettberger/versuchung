# This file is part of versuchung.
# 
# versuchung is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# 
# versuchung is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# versuchung.  If not, see <http://www.gnu.org/licenses/>.

from subprocess import *
from versuchung.files import CSV_File
import logging
import os
import resource
import thread
import time
import pipes
from versuchung.tools import AdviceManager, Advice
from multiprocessing import cpu_count as __cpu_count


try:
    cpu_count = __cpu_count()
except NotImplementedError:
    cpu_count = 1

class CommandFailed(RuntimeError):
    """ Indicates that some command failed

    Attributes:
        command: the command that failed

        returncode:  the exitcode of the failed command
    """
    def __init__(self, command, returncode, stdout=""):
        assert(returncode != 0)
        self.command = command
        self.returncode = returncode
        self.repr = "Command %s failed to execute (returncode: %d)" % \
            (command, returncode)
        self.stdout = stdout
        RuntimeError.__init__(self, self.repr)
    def __str__(self):
        return self.repr + "\n\nSTDOUT:\n" + self.stdout

def quote_args(args):
    if len(args) == 1 and type(args[0]) == dict:
        ret = {}
        for k,v in args[0].items():
            ret[k] = pipes.quote(v)
        return ret
    elif type(args) == list or type(args) == tuple:
        args = tuple([pipes.quote(x) for x in args])
    else:
        assert False
    return args


def __shell(failok, command, *args):
    os.environ["LC_ALL"] = "C"

    args = quote_args(args)
    command = command % args

    logging.debug("executing: " + command)
    p = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
    stdout = ""
    while True:
        x = p.stdout.readline()
        if not x:
            break
        stdout += x
        logging.debug("stdout|%s", x.replace("\n", ""))
    p.wait()
    if len(stdout) > 0 and stdout[-1] == '\n':
        stdout = stdout[:-1]

    if not failok and p.returncode != 0:
        raise CommandFailed(command, p.returncode, stdout)

    return (stdout.__str__().rsplit('\n'), p.returncode)


@AdviceManager.advicable
def shell(command, *args):
    """
    executes 'command' in a shell

    .. note::

      The following command enables capturing `stderr`, `stdout` and
      runtime information (with `/usr/bin/time`)::

        shell.track(experiment.path)

    .. note::

      Tracking is enabled automatically after setup. It can be disabled
      and re-enabled while running the experiment with::

      >> shell.track.disable()
      >> shell.track.enable()

      The tracking feature creates files like ``shell_0_time``,
      ``shell_0_stderr``, and so on. These files are created in the
      ``experiment.path`` directory.

    .. note::

      To write the results of the tracking feature into the experiment
      output folder, use ``self.path`` within a :meth:`run()` method of
      an experiment::

        shell.track(experiment.path)


    :rtype: a tuple with:

        1. the command's standard output as list of lines
        2. the exitcode

    :raises: :exc:`CommandFailed` if the returncode is != 0
    """
    return __shell(False, command, *args)

@AdviceManager.advicable
def shell_failok(command, *args):
    """Like :meth:`.shell`, but the throws no exception"""
    return __shell(True, command, *args)


def add_sys_path(path):
    """Add path to the PATH environment variable"""
    os.environ["PATH"] = path + ":" + os.environ["PATH"]

class AdviceShellTracker(Advice):
    def __call__(self, base_directory):
        self.base_directory = base_directory
        assert os.path.isdir(base_directory)
        self.count = 0
        # Enable the Advice
        self.enable()
        
    def around(self, func, args, kwargs):
        assert len(args) > 0
        command = args[0]
        import versuchung.execute
        args = versuchung.execute.quote_args(list(args)[1:])
        command = command % args

        cmd = "/usr/bin/time --verbose -o %s_time sh -c %s 2> %s_stderr"
        base = os.path.join(self.base_directory, "shell_%d" % self.count)
        self.count += 1
        args = tuple([cmd, base, command, base])

        # Dump away stdout
        ret = func(args, kwargs)
        with open(base + "_stdout", "w+") as fd:
            fd.write("\n".join(ret[0]) + "\n")
        return ret

shell.track =        AdviceShellTracker("versuchung.execute.shell")
shell_failok.track = AdviceShellTracker("versuchung.execute.shell_failok")



class MachineMonitor(CSV_File):
    """Can be used as: **input parameter** and **output parameter**

    With this parameter the systems status during the experiment can
    be monitored. The tick interval can specified on creation and also
    what values should be captured.

    This parameter creates a :class:`~versuchung.files.CSV_File` with
    the given name. When the experiment starts the monitor fires up a
    thread which will every ``tick_interval`` milliseconds capture the
    status of the system and store the information as a row in the
    normal csv.

    A short example::

        class SimpleExperiment(Experiment):
            outputs = {"ps": MachineMonitor("ps_monitor", tick_interval=100)}

            def run(self):
                shell("sleep 1")
                shell("seq 1 100000 | while read a; do echo > /dev/null; done")
                shell("sleep 1")

        experiment = SimpleExperiment()
        experiment(sys.argv)

    >>> experiment.o.ps.extract(["time", "net_send"])
    [[1326548338.701827, 0],
     [1326548338.810422, 3],
     [1326548338.913667, 0],
     [1326548339.016836, 0],
     [1326548339.119982, 2],
     ....

    """
    def __init__(self, default_filename = "", tick_interval=100, capture = ["cpu", "mem", "net", "disk"]):
        CSV_File.__init__(self, default_filename)
        self.tick_interval = tick_interval
        self.__running = True
        self.capture = capture

    def __get_cpu(self):
        return [self.psutil.cpu_percent()]

    def __get_memory(self):
        phymem = self.psutil.phymem_usage()
        virtmem = self.psutil.virtmem_usage()
        cached = self.psutil.cached_phymem()
        buffers = self.psutil.phymem_buffers()

        return [phymem.total, phymem.used, phymem.free,
                virtmem.total, virtmem.used, virtmem.free,
                cached, buffers]

    def __get_net(self):
        if not hasattr(self, "old_network_stat"):
            self.old_network_stat = self.psutil.network_io_counters()
        stat = self.psutil.network_io_counters()
        ret = [stat.bytes_sent - self.old_network_stat.bytes_sent,
               stat.bytes_recv - self.old_network_stat.bytes_recv]
        self.old_network_stat = stat
        return ret

    def __get_disk(self):
        if not hasattr(self, "old_disk_stat"):
            self.old_disk_stat = self.psutil.disk_io_counters()
        stat = self.psutil.disk_io_counters()
        ret = [stat.read_bytes  - self.old_disk_stat.read_bytes,
               stat.write_bytes - self.old_disk_stat.write_bytes]
        self.old_disk_stat = stat
        return ret


    def monitor_thread(self):
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            raise RuntimeError("Please install psutil to use PsMonitor")

        while self.__running:
            row = [time.time()]
            if "cpu" in self.capture:
                row += self.__get_cpu()
            else:
                row += [-1]

            if "mem" in self.capture:
                row += self.__get_memory()
            else:
                row += [-1,-1,-1,-1,-1,-1,-1,-1]

            if "net" in self.capture:
                row += self.__get_net()
            else:
                row += [-1,-1]

            if "disk" in self.capture:
                row += self.__get_disk()
            else:
                row += [-1,-1]

            assert len(row) == len(self.sample_keys)
            self.append(row)


            time.sleep(self.tick_interval/1000.0)

    def inp_extract_cmdline_parser(self, opts, args):
        CSV_File.inp_parser_extract(self, opts, None)
        self.event_file = CSV_File(self.path + ".events")

    def before_experiment_run(self, parameter_type):
        if parameter_type == "output":
            CSV_File.before_experiment_run(self, "output")
            self.event_file = CSV_File(self.path + ".events")
            self.event_file.before_experiment_run("output")
            self.thread = thread.start_new_thread(self.monitor_thread, tuple())

    def after_experiment_run(self, parameter_type):
        if parameter_type == "output":
            self.__running = False
            time.sleep(self.tick_interval/1000.0)
            CSV_File.after_experiment_run(self, "output")
            self.event_file.after_experiment_run("output")


    sample_keys = ["time", "cpu_percentage",
                   "phymem_total", "phymem_used", "phymem_free",
                   "virtmem_total", "virtmem_used", "virtmem_free",
                   "cached", "buffers", "net_send", "net_recv",
                   "disk_read", "disk_write"]

    """The various fields in the csv file are organized like the
    strings in this list. E.g. The unix time is the first field of the
    csv file."""


    def extract(self, keys = ["time", "cpu_percentage"]):
        """Extract single columns from the captured
        information. Useful keys are defined in
        :attr:`~.sample_keys`"""
        indices = [self.sample_keys.index(x) for x in keys]
        ret = []
        for row in self.value:
            r = []
            for index in indices:
                r.append(row[index])
            ret.append(r)
        return ret
