#!/usr/bin/python

import logging
from subprocess import *
import os

def shell(command, *args):
    """
    executes 'command' in a shell

    returns a tuple with
        1. the command's standard output as list of lines
        2. the exitcode
    """
    os.environ["LC_ALL"] = "C"

    args = ["'%s'"%x.replace("'", "\'") for x in args]
    command = command % tuple(args)

    logging.debug("executing: " + command)
    p = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
    (stdout, _)  = p.communicate() # ignore stderr
    if len(stdout) > 0 and stdout[-1] == '\n':
        stdout = stdout[:-1]
    return (stdout.__str__().rsplit('\n'), p.returncode)

