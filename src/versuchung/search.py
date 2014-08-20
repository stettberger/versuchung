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

import os
import logging

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

    for root, dirs, files in os.walk(directory, followlinks=True):
        if "metadata" in files:
            experiment_name = os.path.basename(root)
            path = root
            if experiment_name.startswith(experiment_title):
                dataset = experiment_type(path)
                if selector(dataset):
                    exp = experiment_type(path)
                    if exp.path not in [e.path for e in experiment_map.values()]:
                        experiment_map[experiment_name] = exp

    return experiment_map.values()

def search_experiment(experiment_type, directory, selector = None):
    """Like :func:`search_experiment_results`, but returns only one
    experiment result set. And fails if it is ambigious"""

    exps = search_experiment_results(experiment_type, directory, selector)
    if len(exps) != 1:
        logging.error("search_experiment didn't exactly one instance of %s (%d found)", experiment_type, len(exps))
        for exp in exps:
            logging.error(" - %s", exp.path)
        assert False
    return exps[0]

def search_path_go_up_till(path, till):
    """Go up in the given path (which is of type string), until the
    directory is called till"""

    while path and path != "" and os.path.basename(path) != till:
        path = os.path.dirname(path)
    assert path
    return path


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
