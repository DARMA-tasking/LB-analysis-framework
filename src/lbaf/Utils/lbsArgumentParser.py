"""This module contains argparse ArgumentParser subclass to enable user prompt to help with util or application calls.

PromptArgumentParser: A class that extends the argparse.ArgumentParser class to add the --prompt option to prompt user
                      for argument values
"""
import argparse
import sys
from itertools import repeat
from os import linesep
from typing import Optional, Union

from .lbsColors import blue, green, white_on_red, yellow


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
               required: bool = False, choices: Optional[list] = None):
        """Asks a question"""
        msg = green(question)
        if default is not None:
            msg += " [" + yellow(default) + ']'
        else:
            msg += " [" + blue(None) + ']'

        # The raw_response variable will store the resolved input value
        raw_response = None

        # Ask user until the response value is correct
        while raw_response is None:
            print(msg)
            if choices is not None:
                for index, choice in enumerate(choices):
                    print(" [" + yellow(index) + "]" + ' ' + (blue("None") if choice is None else choice))

            raw_response = input("> ")
            # Empty reponse but default value set default
            if raw_response == '' and default:
                raw_response = default
            # Empty response but no default value set None
            elif raw_response == '' or raw_response == "None":
                raw_response = None
            # Expected bool
            elif value_type == bool:
                raw_response = value_type in ["TRUE", "True", "true", "1"]
            # Else cast if type set
            elif value_type is not None and value_type != str:
                raw_response = value_type(raw_response)

            # Look for choice by choice index or value as input
            if choices is not None:
                for index, choice in enumerate(choices):
                    if raw_response == str(index) or raw_response == choice or \
                            (choice is None and raw_response == "None"):
                        raw_response = choice

            if required is True and raw_response is None:
                print(white_on_red(f"{linesep}{linesep} [ERROR] Value is required{linesep}") + linesep)
            elif choices is not None and raw_response not in choices and raw_response is not None:
                print(white_on_red(
                    f"{linesep}{linesep} [ERROR] Value \"{raw_response}\" is invalid{linesep}") + linesep)
                raw_response = None
            # In case the None response is correct we break the loop
            elif required is False and raw_response is None:
                break

        response = raw_response
        if value_type is not None:
            if callable(value_type):
                response = value_type(raw_response)
        return response

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
