Quick Introduction
******************

As a quick start a simple experiment with input and output parameters is show::

    #!/usr/bin/env python

    from versuchung.experiment import Experiment
    from versuchung.types import String
    from versuchung.files import File

    class SimpleExperiment(Experiment):
        inputs = {"input_key": String("default key"),
                  "input_value": String("default value")}
        outputs = {"output_file": File("output")}

        def run(self):
            # Combine the input parameters
            content = self.inputs.input_key.value \
                + ": " + self.inputs.input_value.value

            # write the result to the output file
            self.outputs.output_file.value = content + "\n"


    if __name__ == "__main__":
        import sys
        experiment = SimpleExperiment()
        dirname = experiment(sys.argv[1:])

        print(dirname)


This experiment is put in a single python script file. It is a
complete experiment and a runnable python script with a command line
parser to override the default experiment input parameters.

Every experiment inherits from the
:class:`~versuchung.experiment.Experiment` class to gain the basic
structure for parameter handling and running the experiment. After
that the member variable
:attr:`~versuchung.experiment.Experiment.inputs` defines a
:class:`dict` of the input parameters. In this case two such input
parameters are defined ``"input_key"`` and ``"input_value"``, which
are both of type :class:`~versuchung.types.String` and have a
specified default value. This default value is used if no argument is
given on the command line. The attribute
:attr:`~versuchung.experiment.Experiment.outputs` defines the
output parameter ``"output_file"`` which is of type
:class:`~versuchung.files.File` with the filename ``"output"``. So
in the experiment output there will be a file called *output*.

The :meth:`~versuchung.experiment.Experiment.run` method is the
heart of every experiment. It is called when all input parameters are
gathered and the experiment environment is set up. In this
``SimpleExperiment`` the input parameters are simply concatenated and
written to the output file. This ``SimpleExperiment`` can be
instantiated without arguments. The resulting object is called with
the command line parameters to enable a command line interface.

Calling ``python experiment.py --help`` gives::

    Usage: experiment.py <options>
    
    Options:
      -h, --help            show this help message and exit
      -d BASE_DIR, --base-dir=BASE_DIR
                            Directory which is used for storing the experiment
                            data
      -l, --list            list all experiment results
      -v, --verbose         increase verbosity (specify multiple times for more)
      --input_key=INPUT_KEY
                            (default: default key)
      --input_value=INPUT_VALUE
                            (default: default value)
    
As you can see the two input parameters can be overwritten on the
command line. The experiment can be executed by ``python
experiment.py`` and print on the console::

    SimpleExperiment-aeb298601cdc582b1b0d8260195f6cfd

This is the versioned experiment result set. The hash at the end is
calculated from the metadata of the experiment (e.g. input parameter
values and the experiment version). In the current directory there was
a directory created with this name where the results are located. To
examine the experiment results and their metadata ``python
experiment.py -l`` can be called::

    +SimpleExperiment-aeb298601cdc582b1b0d8260195f6cfd
    | {'date': '2012-01-14 09:46:13.445703',
    |  'experiment-name': 'SimpleExperiment',
    |  'experiment-version': 1,
    |  'input_key': 'default key',
    |  'input_value': 'default value'}

As you can see there is one result set in the current directory. All
key parameters for the experiment are stored within the ``metadata``
file in the result directory. The ``output`` file in this result
directory contains::

  default key: default value
