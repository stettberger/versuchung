#!/usr/bin/python

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

