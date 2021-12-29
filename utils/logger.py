import logging
import logging.config
import os

from utils.colors import red, green, blue, cyan, magenta, yellow, white, black, light_red, light_green, light_blue, \
    light_cyan, light_magenta, light_yellow, light_white, light_black

_cfg_path = os.path.join(os.path.dirname(__file__), 'logger.ini')
logging.config.fileConfig(_cfg_path)


def logger(name: str = 'root'):
    """ Returns logger with config from logger.ini
    """
    lgr = logging.getLogger(name)
    return lgr


CLRS = {'red': red, 'green': green, 'blue': blue, 'cyan': cyan, 'magenta': magenta, 'yellow': yellow, 'white': white,
        'black': black, 'light_red': light_red, 'light_green': light_green, 'light_blue': light_blue,
        'light_cyan': light_cyan, 'light_magenta': light_magenta, 'light_yellow': light_yellow,
        'light_white': light_white, 'light_black': light_black}
