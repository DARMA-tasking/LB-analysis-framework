#
#@HEADER
###############################################################################
#
#                             lbsArgumentParser.py
#               DARMA/LB-analysis-framework => LB Analysis Framework
#
# Copyright 2019 National Technology & Engineering Solutions of Sandia, LLC
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
"""This module contains argparse ArgumentParser subclass to enable user prompt to help with util or application calls.

PromptArgumentParser: A class that extends the argparse.ArgumentParser class to add the --prompt option to prompt user
                      for argument values
"""
import argparse
import sys
from itertools import repeat
from os import linesep
from typing import Optional, Union, Callable

from .lbsColors import blue, green, white_on_red, white_on_green, yellow, white_on_cyan, cyan


class PromptArgumentParser(argparse.ArgumentParser):
    """An argument parser that adds the --prompt option to prompt user for args"""

    def __init__(self,
                 prog=None,
                 usage=None,
                 description=None,
                 epilog=None,
                 parents=None,
                 formatter_class=argparse.HelpFormatter,
                 prefix_chars='-',
                 fromfile_prefix_chars=None,
                 argument_default=None,
                 conflict_handler="error",
                 add_help=True,
                 allow_abbrev=True,
                 prompt_default: bool = False):

        if parents is None:
            parents = []

        super(PromptArgumentParser, self).__init__(prog, usage, description, epilog, parents, formatter_class,
                                                   prefix_chars, fromfile_prefix_chars, argument_default,
                                                   conflict_handler, add_help, allow_abbrev)

        self._prompt_default = prompt_default

        # add new argument to request argument prompt
        if self._prompt_default:
            self.add_argument("--no-prompt", action="store_false",
                              help="Disables user prompt to enter values for arguments")
        else:
            self.add_argument("--prompt", action="store_true",
                              help="Prompt the user to enter values for all arguments")

    def __print_description(self):
        """Output colored description"""
        length = len(self.description)
        print(''.join(list(repeat(' ', length))))
        print(blue(self.description))
        print(blue(''.join(list(repeat('-', length)))))
        print(''.join(list(repeat(' ', length))))

    def prompt(self, question: str, value_type: Optional[str] = None, default: Optional[Union[str, int, float]] = None,
               required: bool = False, choices: Optional[Union[dict,list]] = None, validate: Optional[Callable] = None):
        """Asks a question"""
        msg = green(question)
        if default is not None:
            msg += " [" + yellow(default) + ']'
        else:
            msg += " [" + blue(None) + ']'

        # The raw_response variable will store the resolved input value
        raw_response = None

        # Ask user until the response value is correct
        while raw_response is None or raw_response == "#error":
            print(msg)

            if choices is not None:
                choices_dict = {index:choice for index, choice in enumerate(choices)} if isinstance(choices, list) else choices
                for index, choice in choices_dict.items():
                    print(" [" + yellow(str(index)) + "]" + ' ' + (blue("None") if choice is None else str(choice)))
            else:
                choices_dict = None

            raw_response = input("> ")
            # Empty reponse but default value set default
            if raw_response == '' and default is not None:
                raw_response = default
            # Empty response but no default value set None
            elif raw_response == '' or raw_response == "None":
                raw_response = None
            # Expected bool
            elif value_type == bool:
                raw_response = True if raw_response in ["TRUE", "True", "true", "1"] else False
            # Else cast if type set
            elif value_type is not None and value_type != str and callable(value_type) and not isinstance(raw_response, value_type):
                try:
                    raw_response = value_type(raw_response)
                except ValueError as ex:
                    self.print_error(f"Input error: {ex.args[0]}")
                    raw_response = "#error"

            # Look for choice by choice index or value as input
            if choices_dict is not None:
                for key, choice in choices_dict.items():
                    if raw_response == str(key) or raw_response == choice or \
                            (choice is None and raw_response == "None"):
                        raw_response = choice

            if required is True and raw_response is None:
                self.print_error(f"Value is required")
            elif choices is not None and raw_response is not None:
                valid_choices = [i for i in choices_dict.values()]
                if raw_response not in valid_choices:
                    self.print_error(f"Value \"{raw_response}\" is invalid")
                    raw_response = None
            # In case the None response is correct we break the loop
            elif required is False and raw_response is None:
                break
            elif validate is not None:
                error = validate(raw_response)
                if error:
                    self.print_error(f"{error}")
                    raw_response = None

        response = raw_response
        return response

    def print_error(self, msg: str):
        """Prints an error message to the console"""
        print(white_on_red(f"{linesep}{linesep} [ERROR] {msg.replace(linesep, linesep + ' ' * 9)}{linesep}") + linesep)

    def print_warning(self, msg: str):
        """Prints a warning message to the console"""
        print(white_on_cyan(f"{linesep}{linesep} [WARNING] {msg.replace(linesep, linesep + ' ' * 11)}{linesep}") + linesep)

    def print_info(self, msg: str):
        """Prints an info message to the console"""
        print(cyan(f"{linesep}[INFO] {msg.replace(linesep, linesep + ' ' * 8)}{linesep}"))

    def print_success(self, msg: str):
        """Prints a success message to the console"""
        print(white_on_green(f"{linesep}{linesep} [SUCCESS] {msg.replace(linesep, linesep + ' ' * 11)}{linesep}") + linesep)

    def set_args(self, args: dict, namespace=None):
        """This method init updates a namespace with the default values and with the given arguments.

        :param args: arguments dictionary to set specific argument values
        """
        if namespace is None:
            namespace = argparse.Namespace()

        # Add any action defaults that aren't present
        for action in self._actions:
            if action.dest is not argparse.SUPPRESS:
                if not hasattr(namespace, action.dest):
                    if action.default is not argparse.SUPPRESS:
                        setattr(namespace, action.dest, action.default)

        # Add any parser defaults that aren't present
        for dest in self._defaults.items():
            if not hasattr(namespace, dest):
                setattr(namespace, dest, self._defaults[dest])

        # Set specific dest values from dict
        for arg in args:
            if not hasattr(namespace, arg):
                setattr(namespace, arg, None)

        return namespace, args

    def parse_known_args(self, args=None, namespace=None):
        """Parse known args.

        :param args: arguments. If dictionary will set args instead of parsing it from the cli.
        """
        if namespace is None:
            namespace = argparse.Namespace()

        if isinstance(args, dict):
            return self.set_args(args, namespace)
        else:
            # check if help is requested then output and exit
            help_requested = "-h" in sys.argv or "--help" in sys.argv
            if help_requested:
                self.print_help()
                raise SystemExit(1)

            # check if prompt is explicitly requested to determine if parsing is needed
            prompt = self._prompt_default
            if prompt is False and "--prompt" in sys.argv:
                prompt = True
            elif prompt is True and "--no-prompt" in sys.argv:
                prompt = False

            if prompt:
                # if prompt
                if self.description is not None:
                    self.__print_description()
                for action in self._actions:
                    if action.dest != "help" and action.dest != "prompt" and action.dest != "no_prompt":
                        question = action.dest + " "
                        question += ":str" if action.type is None else f":{action.type.__name__}"
                        question += ": " + action.help
                        values = self.prompt(question, action.type, action.default, action.required, action.choices)
                        # call the action
                        action(self, namespace, values)
                return namespace, args
            else:
                # if not help requested nor prompt requested just parse cli
                return super(PromptArgumentParser, self).parse_known_args(args, namespace)
