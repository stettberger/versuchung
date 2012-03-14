#!/usr/bin/python

import os

def search_experiment_results(experiment_type, directory, selector = None):
    """In large experiment setups it is hard to keep track of all
    result sets, which were produced. Therefore a search on the
    "result set database" is implemented with this function.

    :param experiment_type: The experiment class object  you are looking for
    :param directory: Which directory to search for (recursivly)
    :param selector: function that gets an experiment_type instance and returns a bool
    :rtype: a list of experiment_type objects

    The selector can also be a :class:`dict` will be wrapped automatically with
    :func:`search_selector_metadata`.

    >>> search_experiment_results(MyExperiment, ".", lambda e: "home" in e.path)
      [<MyExperiment object at 0xb74805ec>]
    """
    # Name -> Path
    experiment_map = {}
    experiment_title = experiment_type.__name__

    if selector == None:
        selector = lambda x: True

    if type(selector) == dict:
        selector = search_selector_metadata(selector)

    for root, dirs, files in os.walk(directory):
        if "metadata" in files:
            experiment_name = os.path.basename(root)
            path = root
            if experiment_name.startswith(experiment_title):
                dataset = experiment_type(path)
                if selector(dataset):
                    experiment_map[experiment_name] = experiment_type(path)

    return experiment_map.values()


def search_selector_metadata(metadata_dict):
    """Creates a selector to be used with
    search_experiment_results. The selector will only select
    experiments where all metadata keys eqyal to the given
    metadata_dict."""
    def selector(experiment):
        for key in metadata_dict:
            if experiment.metadata[key] != metadata_dict[key]:
                return False
        return True
    return selector

def assert_metadata_unique(metadata_field, experiments):
    """Ensure that all experiments have a different value in their
    metadata according to the metadata_field"""
    fields = set()
    for e in experiments:
        field = e.metadata[metadata_field]
        assert not field in fields
        fields.add(field)

def assert_metadata_common(metadata_field, experiments):
    """Ensure that all experiments have the same value in their
    metadata according to the metadata_field"""
    if len(experiments) > 1:
        field = experiments[0].metadata[metadata_field]
        for e in experiments:
            assert field == e.metadata[metadata_field]

if __name__ == '__main__':
    import sys
    from versuchung.experiment import Experiment
    if len(sys.argv) != 4:
        print "%s <experiment-type> <field> <data>" % sys.argv[0]
        sys.exit(-1)
    Experiment.__name__ = sys.argv[1]
    for exp in search_experiment_results(Experiment, ".", {sys.argv[2]: sys.argv[3]}):
        print exp.path
