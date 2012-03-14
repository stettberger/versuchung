Search result sets as input parameters
**************************************

In large experiment setups it is challenging to keep track of all
result sets that are floating arround. This is especially true, if you
want to select result sets according to the metadata as input
parameters for other experiments.

Imagine you have a set of "InferenceResults", which have the key
"arch" in their metadata. And you want to select an instance of these
result sets as an input parameter. This is possible when using
functions as input parameters.

If an input parameter is a function, it will be called with the
experiment instance as first argument, after all other parameters are
parsed (from the command line)::

   from versuchung.search import *

   inputs = {
       "arch": String("x86"),
        
        # Here come computed arguments
        "inference_s390": lambda self:\
              search_experiment(InferenceResults,
                              search_path_go_up_till(self.base_directory, "data"),
                              {'arch': "s390"}),

        "inference": lambda self:\
              search_experiment(InferenceResults,
                              search_path_go_up_till(self.base_directory, "data"),
                              {'arch': self.arch.value}),
   } 

Here two inputs are computed. inference_s390 is calulated dynamically,
but isn't dependend on any other input parameter. The result set is
search an directory, which is an upper directory to the current one,
and is named "data".

The inference parameter is similar, but dependent on the "arch" input
parameter.

.. automodule:: versuchung.search
   :members:
