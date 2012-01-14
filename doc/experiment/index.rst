Defining a Experiment
*********************

As every experiment *must* inherit from the
``versuchung.experiment.Experiment`` class their attributes and methods are absolutly basic to versuchung.

.. autoclass:: versuchung.experiment.Experiment
   :members: __init__, version, title, name, i, inputs, o, outputs, run, execute, __call__
