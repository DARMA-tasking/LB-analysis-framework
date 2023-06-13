"""module providing input and output methods useful for scripts with interations"""

from pydoc import locate
from typing import Optional, Union
from itertools import repeat

from lbaf.Utils.colors import green, yellow, blue


def title(text):
    """Output some title text"""
    print(''.join(list(repeat(' ', len(text)))))
    print(yellow(''.join(list(repeat('=', len(text))))))
    print(yellow(text))
    print(yellow(''.join(list(repeat('=', len(text))))))
    print(''.join(list(repeat(' ', len(text)))))

def info(text: str):
    """Output some information text"""
    print(blue(text))

def ask(question: str, value_type: Optional[str] = None, default: Optional[Union[str,int,float]] = None, required: bool = False):
    """Asks a question""" 
    msg = green(question)
    if default is not None:
        msg += " " + yellow(f"[{default}]")

    raw_response = None

    while raw_response is None:
        print(msg)
        raw_response = input("> ")
        # set default if no response given
        if raw_response == '' and default:
            raw_response = default
        # consider empty response as None
        if raw_response == '':
            raw_response = None

        if required is False and raw_response is None:
            break

    response = raw_response
    if value_type is not None:
        if callable(value_type):
            response = value_type(raw_response)
    return response

# def ask_choice(self, question: str, choices: list):
#     """Asks for a question"""
#     response = input(green(question))
