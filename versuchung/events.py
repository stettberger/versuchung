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

from versuchung.files import CSV_File
from versuchung.execute import shell
import logging
import os
import time

class EventLog(CSV_File):
    """Log events with timestamp"""
    def event(self, event, key, value = ""):
        """Log a event to the event log. There the event and the
        description together with the time of the event is stored

        :return: float -- UNIX Time of the Event"""
        t = time.time()
        self.append([t, event, key, value])
        return t

    def shell(self, command, *args):
        """Like :func:`~versuchung.execute.shell`, but logs the start
        and stop of the process in the ``".events"``-file."""

        _args = ["'%s'"%x.replace("'", "\'") for x in args]
        _command = command % tuple(_args)

        start = self.event("process started", _command)
        shell(command, *args)
        stop = self.event("process finished", _command)
        self.event("process duration", _command, stop - start)

