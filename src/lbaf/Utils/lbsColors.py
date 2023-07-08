"""src/lbaf/Utils/colors.py"""
import colorama


def __make_colorizer(color, bg_color=colorama.Back.RESET):
    def colored(s, style=None):
        s = color + bg_color + str(s)
        if style is None:
            pass
        elif style.upper() == "DIM":
            s = colorama.Style.DIM + s
        elif style.upper() == "BRIGHT":
            s = colorama.Style.BRIGHT + s
        return s + colorama.Style.RESET_ALL
    return colored


red = __make_colorizer(colorama.Fore.RED)
green = __make_colorizer(colorama.Fore.GREEN)
blue = __make_colorizer(colorama.Fore.BLUE)
cyan = __make_colorizer(colorama.Fore.CYAN)
magenta = __make_colorizer(colorama.Fore.MAGENTA)
yellow = __make_colorizer(colorama.Fore.YELLOW)
white = __make_colorizer(colorama.Fore.WHITE)
black = __make_colorizer(colorama.Fore.BLACK)
light_red = __make_colorizer(colorama.Fore.LIGHTRED_EX)
light_green = __make_colorizer(colorama.Fore.LIGHTGREEN_EX)
light_blue = __make_colorizer(colorama.Fore.LIGHTBLUE_EX)
light_cyan = __make_colorizer(colorama.Fore.LIGHTCYAN_EX)
light_magenta = __make_colorizer(colorama.Fore.LIGHTMAGENTA_EX)
light_yellow = __make_colorizer(colorama.Fore.LIGHTYELLOW_EX)
light_white = __make_colorizer(colorama.Fore.LIGHTWHITE_EX)
light_black = __make_colorizer(colorama.Fore.LIGHTBLACK_EX)

white_on_red = __make_colorizer(colorama.Fore.WHITE, colorama.Back.RED)

colorama.init()
