"""This module runs pylint and if no specific output format 
is requested formats the output for Github Actions"""

import sys
from pathlib import Path
from pylint import lint
from pylint.reporters import CollectingReporter
from actions_toolkit import core

argv = sys.argv
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
    if not a.startswith('-'):
        p = Path(a)
        if not p.is_absolute():
            a = p.resolve().as_posix()
    args.append(a)

report = CollectingReporter()
result = lint.Run(
    args,
    reporter=report,
    do_exit=False
)

level:str = None
for error in report.messages:
    if error.category in ["error", "fatal"]:
        core.error(f"{error.msg} ({error.msg_id})", start_line=error.line, end_line=error.end_line, start_column=error.column, end_column=error.end_column)
    else:
        core.warning(f"{error.msg} ({error.msg_id})", start_line=error.line, end_line=error.end_line, start_column=error.column, end_column=error.end_column)