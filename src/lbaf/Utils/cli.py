"""module providing some input and output methods for the CLI
- title: to display a text in a king of title style
- info: to display text in blue
- ask: to request a user input
"""
from typing import Optional, Union
from itertools import repeat
from os import linesep

from .colors import green, yellow, blue, white_on_red


def title(text):
    """Output some title text"""
    print(''.join(list(repeat(' ', len(text)))))
    print(yellow(''.join(list(repeat('=', len(text))))))
    print(yellow(text))
    print(yellow(''.join(list(repeat('=', len(text))))))
    print(''.join(list(repeat(' ', len(text)))))


def ask(question: str, value_type: Optional[str] = None, default: Optional[Union[str,int,float]] = None,
    required: bool = False, choices: Optional[list] = None):
    """Asks a question"""
    msg = green(question)
    if default is not None:
        msg += " [" + yellow(default) + ']'

    raw_response = None

    while raw_response is None:
        print(msg)
        if choices is not None:
            for index, choice in enumerate(choices):
                print(' [' + yellow(index) + ']' + ' ' + (blue('None') if choice is None else choice) )

        raw_response = input("> ")
        # set default if no response given and if default given
        if raw_response == '' and default:
            raw_response = default
        elif choices is not None:
            for index, choice in enumerate(choices):
                if raw_response == str(index) or raw_response == choice or (choice is None and raw_response == "None"):
                    raw_response = choice
        # consider empty response as None
        if raw_response == '' or raw_response == "None":
            raw_response = None

        if required is True and raw_response is None:
            print(white_on_red(f"{linesep}{linesep} [ERROR] Value is required{linesep}") + linesep)
        elif choices is not None and raw_response not in choices and raw_response is not None:
            print(white_on_red(f"{linesep}{linesep} [ERROR] Value \"{raw_response}\" is invalid{linesep}") + linesep)
            raw_response = None
        elif required is False and raw_response is None:
            break

    print(linesep)
    response = raw_response
    if value_type is not None:
        if callable(value_type):
            response = value_type(raw_response)
    return response
