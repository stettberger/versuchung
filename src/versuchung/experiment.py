#!/usr/bin/python

from optparse import OptionParser
import datetime
import logging
import pprint
from versuchung.types import InputParameter, OutputParameter, Type
import sys, os
import hashlib
import shutil

class Experiment(Type, InputParameter):
    def __init__(self, default_experiment_instance = None):
        self.title = self.__class__.__name__
        self.__experiment_instance = default_experiment_instance

    def __setup_parser(self):
        self.__parser = OptionParser("%prog <options>")
        self.__parser.add_option('-l', '--list', dest='do_list', action='store_true',
                                 help="list all experiment results")
        self.__parser.add_option('-v', '--verbose', dest='verbose', action='count',
                                 help="increase verbosity (specify multiple times for more)")

        for (name, inp) in self.inputs.items():
            if not isinstance(inp, InputParameter):
                print "%s cannot be used as an input parameter" % name
                sys.exit(-1)
            inp.name = name
            inp.inp_setup_cmdline_parser(self.__parser)

    def __call__(self, args):
        self.__setup_parser()
        (opts, args) = self.__parser.parse_args(args)
        self.pwd = os.path.abspath(os.curdir)

        if opts.do_list:
            for experiment in os.listdir(self.pwd):
                if experiment.startswith(self.title):
                    self.__do_list(self.__class__(experiment))
            return


        for (name, inp) in self.inputs.items():
            inp.base_directory = self.pwd
            ret = inp.inp_extract_cmdline_parser(opts, args)
            if ret:
                (opts, args) = ret

        self.__experiment_instance = self.__setup_output_directory()
        self.__output_directory = os.path.join(self.pwd, self.__experiment_instance)

        for (name, outp) in self.outputs.items():
            if not isinstance(outp, OutputParameter):
                print "%s cannot be used as an output parameter" % name
                sys.exit(-1)
            outp.name = name
            outp.base_directory = self.__output_directory
            outp.outp_setup_output()

        self.run()

        for (name, outp) in self.outputs.items():
            outp.outp_tear_down_output()

        return self.__experiment_instance


    def __do_list(self, experiment, indent = 0):
        with open(os.path.join(experiment.__experiment_instance, "metadata")) as fd:
            content = fd.read()
        d = eval(content)
        print "+%s%s" % (" " * indent,
                        content.strip().replace("\n", "\n|" + (" " * indent)))
        for dirname in os.listdir("."):
            if dirname in d.values():
                self.__do_list(Experiment(dirname), indent + 3)

    def __setup_output_directory(self):
        metadata = {}
        for name in self.inputs:
            metadata.update( self.inputs[name].inp_metadata() )
        m = hashlib.md5()
        m.update("version %d" % self.version)
        for key in sorted(metadata.keys()):
            m.update(key + " " + metadata[key])

        self.__experiment_instance = "%s-%s" %(self.title, m.hexdigest())
        output_path = os.path.join(self.pwd, self.__experiment_instance)
        if os.path.exists(output_path):
            logging.info("Output directory existed already, purging it")
            shutil.rmtree(output_path)

        os.mkdir(output_path)

        # Here the hash is already calculated, so we can change the
        # metadata nonconsitent
        metadata["date"] = str(datetime.datetime.now())
        metadata["experiment-name"] = self.title
        metadata["experiment-version"] = self.version

        fd = open(os.path.join(output_path, "metadata"), "w+")
        fd.write(pprint.pformat(metadata) + "\n")
        fd.close()

        return self.__experiment_instance

    ### Input Type
    def inp_setup_cmdline_parser(self, parser):
        self.inp_parser_add(parser, None, self.__experiment_instance)
    def inp_extract_cmdline_parser(self, opts, args):
        self.__experiment_instance = self.inp_parser_extract(opts, None)
        if not self.__experiment_instance:
            print "Missing argument for %s" % self.title
        for (name, outp) in self.outputs.items():
            outp.base_directory = os.path.join(self.base_directory, self.__experiment_instance)
    def inp_metadata(self):
        return {self.title: self.__experiment_instance}
