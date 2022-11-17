#!/usr/bin/python3
import os
import sys
import shutil
import datetime
import logging

def transitive_hull(experiments, from_metadata=False):
    good = set()
    roots = list(experiments)
    while roots:
        item = roots.pop()
        item = os.path.relpath(item)
        if not os.path.exists(item):
            continue
        if not os.path.exists(os.path.join(item, 'metadata')):
            continue
        if item in good:
            continue
        good.add(item)
        if os.path.islink(item):
            roots.append(os.path.realpath(item))

        if not from_metadata:
            continue

        m = eval(open(os.path.join(item, "metadata")).read())
        for value in m.values():
            if type(value) is str:
                roots.append(value)
    return good

def print_list(items, verbose = False):
    symlinks = [x for x in items if os.path.islink(x)]
    deref    = [os.path.realpath(x) for x in symlinks]
    items =    [x for x in items if os.path.abspath(x) not in deref]

    max_name = max(*[len(x) for x in items])

    lines = []
    total_runtime = None
    for item in sorted(items, key = lambda x: (x not in symlinks, x)):
        metadata_path = os.path.join(item, "metadata")
        if not os.path.exists(metadata_path):
            continue

        if not verbose:
            print(item)
            continue

        # With verbosity
        with open(metadata_path) as fd:
            try:
                metadata = eval(fd.read())
            except:

                lines.append([item, 'broken'])
                continue
        if 'date-end' not in metadata:
            lines.append([item, 'incomplete',
                          "(begin: %s)"%metadata['date-start']])
            continue
        start = datetime.datetime.strptime(metadata['date-start'], "%Y-%m-%d %H:%M:%S.%f")
        end   = datetime.datetime.strptime(metadata['date-end'], "%Y-%m-%d %H:%M:%S.%f")
        delta = end-start
        delta = datetime.timedelta(delta.days, delta.seconds) # Drop microseconds

        if total_runtime:
            total_runtime += delta
        else:
            total_runtime = delta

        lines.append([item, 'ok', str(delta)])
    align = 0
    for line in lines:
        align = max(align, len(line[0]))
    for line in lines:
        print("{0:<{1}}".format(line[0], align), *line[1:])

    print("Total Runtime: ", total_runtime)

def main(argv):
    p = os.path.realpath(__file__)
    p = os.path.abspath(p)
    p = os.path.dirname(os.path.dirname(p))
    sys.path.append(p)
    if len(argv) < 1:
        print(f"usage: {sys.argv[0]} <CMD | ipynb>")
        print("")
        print("\tls     - List all experiment results in this directory")
        print("\tgc     - Results that are not referenced by symlink or from metadata")
        print("\tipynb  - Run Jupyter Notebook as experiment")
        sys.exit(1)

    if argv[0] == "gc":
        if len(sys.argv) > 1 and sys.argv[1] == '-v':
            del sys.argv[1]
            verbose = True
        else:
            verbose = False
        roots = sys.argv[1:]
        if not roots:
            roots = [x for x in os.listdir(".") if os.path.islink(x)]

        good = transitive_hull(roots, from_metadata=True)
        items = set(os.listdir(".")) - good

        print_list(items, verbose=verbose)

    elif argv[0] == "ls":
        print_list(os.listdir("."), verbose=True)

    elif argv[0].endswith(".ipynb"):
        import papermill as pm
        from tempfile import NamedTemporaryFile
        from nbconvert import HTMLExporter

        output = NamedTemporaryFile(suffix=".ipynb")
        path = NamedTemporaryFile(mode="r+")
        nb = pm.execute_notebook(
            input_path=argv[0],
            output_path=output.name,
            cwd=os.path.dirname(os.path.join(".", argv[0])),
            report_mode=True,
            log_output=True,
            stdout_file=sys.stdout,
            stderr_file=sys.stderr,
            progress_bar=False,
            parameters=dict(versuchung_args=argv[1:],
                            versuchung_path=path.name))

        # Copy Output Jupyter Notebook to directory
        experiment_dir = path.read()
        if not experiment_dir:
            raise RuntimeError("Notebook does not experiment path. Did you call experiment.begin()")
        dst = os.path.join(experiment_dir, os.path.basename(argv[0]))
        with open(dst, "wb+") as ipynb:
            ipynb.write(output.read())

        html_exporter = HTMLExporter(template_name = 'classic')
        (body, resources) = html_exporter.from_notebook_node(nb)
        with open(dst +".html", "w+") as html:
            html.write(body)
        return experiment_dir

    elif argv[1] == "cp":
        if len(sys.argv) < 3:
            print("versuchung gc <dst 1> [<dst 2>...] <dst>")
            sys.exit(-1)
        roots = sys.argv[2:-1]
        target = sys.argv[-1]
        if os.path.exists("%s/metadata" % target):
            print("ERROR: target is an experiment instance. Forgot dst?")
            sys.exit(-1)
        srcs = transitive_hull(roots)
        for src in sorted(srcs):
            dst = os.path.join(target, src)
            if os.path.islink(src):
                if os.path.islink(dst):
                    os.unlink(dst)
                value = os.readlink(src)
                os.symlink(value, dst)
            else:
                if os.path.exists(dst):
                    print("WARN: %s already exists" % src)
                    continue
                else:
                    shutil.copytree(src, dst)
            print("%s -> %s/"% (src, target))
    else:
        main([])

if __name__ == "__main__":
    main(sys.argv[1:])
