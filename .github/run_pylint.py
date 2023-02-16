"""This module runs pylint and if no specific output format 
is requested formats the output for Github Actions"""

import sys
from urllib.parse import quote_plus
from pathlib import Path
from actions_toolkit import core
from pylint import lint
from pylint.reporters import CollectingReporter

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
    # many messages do not appear in Github Action annotations.
    # by quoting message we try to eliminate possible invalid characters
    msg = error.msg.replace('\"', "%22").replace("\'", "%27")
    if error.category in ["error", "fatal"]:
        core.error(f"{msg} ({error.msg_id})", file=error.path, start_line=error.line, end_line=error.end_line, start_column=error.column, end_column=error.end_column)
    else:
        core.warning(f"{msg} ({error.msg_id})", file=error.path, start_line=error.line, end_line=error.end_line, start_column=error.column, end_column=error.end_column)