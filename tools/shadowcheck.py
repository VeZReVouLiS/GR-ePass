"""Catch attributes that shadow methods of the same name.

`self._amount = 5` in __init__ and `def _amount(self)` further down are both
legal Python, import cleanly, and pass every linter -- then `self._amount()`
raises "'NoneType' object is not callable" at the one moment that matters.
That is exactly how the top-up button broke in 0.10.0, so it gets a check.
"""

import ast
import io
import os
import sys

# The component targets Home Assistant's Python. Parsing it with an older one
# would raise SyntaxError on `type X = ...` and friends, and a check that
# silently skips the files it cannot read is worse than no check at all.
if sys.version_info < (3, 12):
    sys.exit("shadowcheck needs Python 3.12+ (run: py -3.14 tools/shadowcheck.py)")

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "custom_components", "gr_epass")
problems = []


def assigned_names(cls):
    """Every name assigned as self.<name> anywhere in the class."""
    names = set()
    for node in ast.walk(cls):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        for target in targets:
            if (isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"):
                names.add(target.attr)
    return names


for folder, _, files in os.walk(ROOT):
    for name in sorted(files):
        if not name.endswith(".py"):
            continue
        path = os.path.join(folder, name)
        tree = ast.parse(io.open(path, encoding="utf-8").read(), path)
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            methods = {}
            for item in cls.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    decorators = {d.id for d in item.decorator_list
                                  if isinstance(d, ast.Name)}
                    # A property is meant to be read as an attribute; only plain
                    # methods are called, so only those can break this way.
                    if "property" not in decorators:
                        methods[item.name] = item.lineno
            for clash in sorted(set(methods) & assigned_names(cls)):
                problems.append("%s:%d %s.%s is both a method and an attribute"
                                % (os.path.relpath(path, ROOT), methods[clash],
                                   cls.name, clash))

for line in problems:
    print(" ", line)
print("shadowing:", "none" if not problems else "%d found" % len(problems))
sys.exit(1 if problems else 0)
