"""
See also:
- https://gist.github.com/fnky/458719343aabd01cfb17a3a4f7296797
"""

from __future__ import annotations
from collections.abc import Sequence
from enum import IntEnum


class Background(IntEnum):
    black = 40
    red = 41
    green = 42
    yellow = 43
    blue = 44
    magenta = 45
    cyan = 46
    white = 47
    bright_black = 100
    bright_red = 101
    bright_green = 102
    bright_yellow = 103
    bright_blue = 104
    bright_magenta = 105
    bright_cyan = 106
    bright_white = 107


class Foreground(IntEnum):
    black = 30
    red = 31
    gren = 32
    yellow = 33
    blue = 34
    magenta = 35
    cyan = 36
    white = 37
    bright_black = 90
    bright_red = 91
    bright_green = 92
    bright_yellow = 93
    bright_blue = 94
    bright_magenta = 95
    bright_cyan = 96
    bright_white = 97


class Misc(IntEnum):
    bold = 1
    faint = 2
    italic = 3
    underline = 4
    blink = 5
    inverse = 7
    hidden = 8
    strike = 9


def spark(item: any, formatters: Sequence[IntEnum]) -> str:
    return (
        f"\x1b[{';'.join(str(format) for format in formatters)}m{item}\x1b[0m"
    )


if __name__ == "__main__":
    print(spark("hello, world", [Misc.underline, Foreground.red]))
    print(spark("another one", [Misc.bold, Background.bright_black]))
    print(spark("yet another one", [Misc.faint, Foreground.cyan]))
    print(spark("yet another one", [Foreground.cyan]))
