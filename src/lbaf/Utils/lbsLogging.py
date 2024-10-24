#
#@HEADER
###############################################################################
#
#                                lbsLogging.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019-2024 National Technology & Engineering Solutions of Sandia, LLC
# (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S.
# Government retains certain rights in this software.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Questions? Contact darma@sandia.gov
#
###############################################################################
#@HEADER
#
"""This module contains logging utility method to create and get loggers"""
import logging
import os
from typing import Union, List, Dict

from .lbsColors import red, green, cyan, yellow


LOGGING_LEVEL = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "FATAL": logging.FATAL
}
FORMAT_BASIC = "basic"
""""%(levelname)s [%(module)s.%(funcName)s()] %(message)s"""
FORMAT_EXTENDED = "extended"
""""%(levelname)s [%(module)s.%(funcName)s()] [%(message)s]"""
FORMATS = [FORMAT_BASIC, FORMAT_EXTENDED]
Logger = logging.Logger
"""Logger class alias to the logging Logger class"""


class CustomFormatter(logging.Formatter):
    """Formatter able to write colored logs.

    Colors are used to colorize log meta information such as:
    - the calling module name
    - the caling function name (available with 'extended' format only)
    - logging level (available with 'extended' format only)
    """

    LOGGING_LEVEL_COLORS = {
        logging.DEBUG: yellow,
        logging.INFO: green,
        logging.WARNING: cyan,
        logging.ERROR: red,
        logging.FATAL: red
    }

    _raw_formatter: None
    _color_formatters: Dict[int, logging.Formatter] = {}
    _format: Union[FORMAT_BASIC, FORMAT_EXTENDED]
    _colored: bool = False

    def __init__(self, frmt: str, colored: bool = False):
        super().__init__()

        if not frmt in FORMATS:
            formats = str.join(', ', FORMATS)
            raise ValueError(f"Invalid format. Supported are {formats}")

        self._colored = colored
        self._format = frmt
        self._init_formatters()

    def _init_formatters(self):
        """Initialize inner formatters for each supported logging level."""

        # 'basic' default format
        formats = {"prefix": "[%(module)s] ", "message": "%(message)s"}
        # 'extended' format
        if self._format == "extended":
            formats = {"prefix": "%(levelname)s [%(module)s.%(funcName)s()] ", "message": "msg:[%(message)s]"}

        # Create inner formatter for each log level
        if self._colored:
            for level, colorizer in self.LOGGING_LEVEL_COLORS.items():
                self._color_formatters[level] = logging.Formatter(
                    colorizer(formats.get("prefix")) + formats.get("message")
                )
        # Or create raw formatter to use at any level
        else:
            self._raw_formatter = logging.Formatter(formats.get("prefix") + formats.get("message"))

    def format(self, record):
        formatter = None
        if self._colored:
            formatter = self._color_formatters[
                record.levelno
                if record.levelno in self.LOGGING_LEVEL_COLORS
                else logging.INFO
            ]
        else:
            formatter = self._raw_formatter
        return formatter.format(record)


loggers = {}
"""Dictionary of loggers registered by the get_logger function where the key is the name of the logger"""


def get_logger(
        name: str = "root",
        level: Union[str, None] = "info",
        log_to_console: bool = True,
        log_to_file: Union[str, None] = None,
        frmt: str = FORMAT_BASIC
) -> Logger:
    """Return a new or an existing logger."""
    if name in loggers:
        return loggers[name]

    # Init new logger
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level.upper())

    # Index logger for future usage
    loggers[name] = logger

    # Clear default handlers
    logging.getLogger().handlers.clear()

    # Init log directory if logging to file
    if log_to_file is not None:
        logs_dir = f"{os.sep}".join(log_to_file.split(os.sep)[:-1])
        if not os.path.isdir(logs_dir):
            os.makedirs(logs_dir)

    # Initialize handlers
    handlers = logger.handlers
    handlers = []  # type: List[logging.Handler]
    if isinstance(log_to_file, str):
        handlers.append(logging.FileHandler(filename=log_to_file))
    if log_to_console:
        handlers.append(logging.StreamHandler())
    for handler in handlers:
        handler.setLevel(logger.level)
        # Use color formatter only if console
        handler.setFormatter(CustomFormatter(frmt, colored=isinstance(handler, logging.StreamHandler)))
        logger.addHandler(handler)

    return logger
