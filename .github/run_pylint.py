"""This module runs pylint and if no specific output format 
is requested formats the output for Github Actions"""

import sys
from pathlib import Path
from pylint import lint
from pylint.reporters import CollectingReporter
from actions_toolkit import core

argv = sys.argv[0]

args = [ ]
# DEBUG TEST
# argv = [
#     "/run_pylint.py",
#     "/workspaces/LB-analysis-framework/src",
#     "--rcfile=/workspaces/LB-analysis-framework/.pylintrc"
# ]
for i, a in enumerate(argv):
    if i == 0:
        continue
    if a.startswith("--output-format="):
        raise Exception('--output-format option is not authorized here')
    elif (not a.startswith('-')):
        p = Path(a)
        if (not p.is_absolute()):
            a = p.resolve().as_posix()
    args.append(a)

# def print_github_message(text :str):
#     """Output a string with url-encoded eol"""
#     if "\n" in text:
#         text = text.replace("\n", "%0A")
#     print(msg)
    

report = CollectingReporter()
result = lint.Run(
    args,
    reporter=report,
    do_exit=False
)

level:str = None
for error in report.messages:
    if error.category in ["error", "fatal"]:
        level = "error"
    else:
        level = "warning"
    msg = f"::{level} file={error.path}"
    if error.line is not None:
        msg += f",line={error.line}"
    if error.column is not None:
        msg += f",col={error.column}"
    if error.end_column is not None:
        msg += f",endColumn={error.end_column}"
    msg += "::"
    if error.msg:
        msg += error.msg
    if error.msg_id:
        msg += f" ({error.msg_id})"

    core.warning(msg)
    # print_github_message(msg)
