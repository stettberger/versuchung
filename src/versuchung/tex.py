#!/usr/bin/python

from versuchung.files import File
import re

class Macros(File):
    def __init__(self, filename = "data.tex"):
        """Define tex macros directly as output of a experiment.

        Use this only as output parameter!."""
        File.__init__(self, filename)

    def macro(self, macro, value):
        """Define a new tex macro with \\necommand"""

        self.write("\\newcommand{\\%s} {%s}\n" % (macro, value), append = True)

    def comment(self, comment):
        """Add a comment in the macro file"""
        for line in comment.split("\n"):
            self.write("%% %s\n" % line.strip(), append = True)

    def newline(self):
        """Append an newline to the texfile"""
        self.write("\n", append = True)


class PgfKeyDict(File, dict):
    __format = r'\pgfkeyssetvalue{%s}{%s}'

    def __init__(self, filename = "data.tex", pgfkey = "versuchung"):
        """Define tex macros directly as output of a experiment.

        Use this only as output parameter!."""
        self.__pgfkey = pgfkey

        File.__init__(self, filename)
        dict.__init__(self)

    def after_read(self, value):
        regex = self.__format %("([^{}]*)", "([^{}]*)")
        regex.replace(r'\\', r'\\')
        for line in value.split("\n"):
            m = re.search(regex, line)
            if m:
                self[m.groups()[0]] = m.groups()[1]
        return self

    def before_write(self, value):
        v = [self.__format % (key, value) for (key, value) in self.items()]
        return "\n".join(v)

