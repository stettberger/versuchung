#!/usr/bin/python

from versuchung.files import File
import re
import os

class Macros(File):
    """Can be used as: **input parameter** and **output parameter**

    A Macros file is a normal :class:`~versuchung.files.File` with the
    extension, that you can define TeX macros easily. This is
    especially useful for writing texts. You may have a experiment,
    which may be an analysis to an experiment that produces raw
    data. The produced numbers should appear in your LaTeX
    document. So instead of copying the numbers you can define TeX
    macros and use them in the text. This is especially useful if you
    work on the experiment and the text in parallel and the numbers
    change often.

    >>> from versuchung.tex import Macros
    >>> macro = Macros("/tmp/test.tex")
    >>> macro.macro("MyNewTexMacro", 23)
    >>> print macro.value
    \\newcommand{\MyNewTexMacro} {23}

    """
    def __init__(self, filename = "data.tex"):
        """Define tex macros directly as output of a experiment.

        Use this only as output parameter!."""
        File.__init__(self, filename)

    def macro(self, macro, value):
        """Define a new tex macro with \\\\newcommand. This will result in::

            \\newcommand{%(macro)s} { %(value)s}

        """

        self.write("\\newcommand{\\%s} {%s}\n" % (macro, value), append = True)

    def comment(self, comment):
        """Add a comment in the macro file"""
        for line in comment.split("\n"):
            self.write("%% %s\n" % line.strip(), append = True)

    def newline(self):
        """Append an newline to the texfile"""
        self.write("\n", append = True)


class PgfKeyDict(File, dict):
    """Can be used as: **input parameter** and **output parameter**

    PgfKeyDict is very similar to :class:`~versuchung.tex.Macros`, but
    instead of \\\\newcommand directives it uses pgfkeys, can be used
    as a ``dict`` and it is possible to read it in again to produce
    the (almost) same dict again.

    >>> from versuchung.tex import PgfKeyDict
    >>> pgf = PgfKeyDict("/tmp/test.tex")
    >>> pgf["abcd"] = 23
    >>> pgf.flush()  # flush method of File
    >>> print open("/tmp/test.tex").read()
    \\pgfkeyssetvalue{/versuchung/abcd}{23}

    In the TeX source you can do something like::

      \\usepackage{tikz}
      \\pgfkeys{/pgf/number format/.cd,fixed,precision=1}
      [...]
      \\newcommand{\\versuchung}[1]{\\pgfkeysvalueof{/versuchung/#1}}
      \\versuchung{abcd}

    .. note::

       It is better to use :class:`PgfKeyDict` instead of :class:`Macros`, because
       you can also use spaces and other weird characters in pgfkeys,
       which cannot be used in TeX macro names.
    """

    __format = r'\pgfkeyssetvalue{/%s/%s}{%s}'

    def __init__(self, filename = "data.tex", pgfkey = "versuchung"):
        self.__pgfkey = pgfkey

        File.__init__(self, filename)
        dict.__init__(self)

        # Ensure the file is written
        if os.path.exists(self.path):
            a = self.value

    def after_read(self, value):
        regex = self.__format %(self.__pgfkey,"([^{}]*)", "([^{}]*)")
        regex.replace(r'\\', r'\\')
        for line in value.split("\n"):
            m = re.search(regex, line)
            if m:
                self[m.groups()[0]] = m.groups()[1]
        return self

    def before_write(self, value):
        v = []
        last_base_key = None
        for key in sorted(self):
            value = self[key]
            if "/" in key:
                base_key = key[:key.rindex("/")]
            else:
                base_key = None
            if last_base_key and last_base_key != base_key:
                v.append("")
            last_base_key = base_key
            v.append(self.__format % (self.__pgfkey, key, value))

        return "\n".join(v) + "\n"

    def flush(self):
        self.value = self.before_write(self)
        File.flush(self)


if __name__ == '__main__':
    import sys
    print PgfKeyDict(sys.argv[1])
