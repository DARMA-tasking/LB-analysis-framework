#
#@HEADER
###############################################################################
#
#                                 lbsColors.py
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
white_on_green = __make_colorizer(colorama.Fore.WHITE, colorama.Back.GREEN)
white_on_cyan = __make_colorizer(colorama.Fore.CYAN, colorama.Back.CYAN)

colorama.init()
