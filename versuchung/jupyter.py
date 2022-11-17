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

from versuchung.experiment import Experiment

class JupyterExperiment(Experiment):
      def __init__(self, title, *args, **kwargs):
            Experiment.__init__(self, *args, title=title, **kwargs)

      def execute(self):
            raise RuntimeError("Please use begin()/end()")

      def begin(self, args=[], globals=None):
            if globals is None:
                  raise RuntimeError("Please specify globals=globals()")
            self._globals = globals
            args = args + self._globals.get('versuchung_args', [])
            self.execute_setup(args)
            out = self._globals.get('versuchung_path')
            if out:
                  with open(out, "w+") as fd:
                        fd.write(self.path)

      def end(self):
            self.execute_teardown()

