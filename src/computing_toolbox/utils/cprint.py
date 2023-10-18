"""Color Print functions
able to print to stdout for std messages
and with colors for warning, error, success and info messages

there is one option to print as a ascii-art characters as well.
"""
import os
import sys

import art
import colorama

colorama.init(autoreset=True)


class CPrint:
    """ColorPrint class"""

    @classmethod
    def output_buffering(cls, flag: bool = True):
        """set or unset python output buffering """
        if not flag:
            # unset buffering or set un-buffering
            os.environ["PYTHONUNBUFFERED"] = '1'
        else:
            # set buffering or unset un-buffering
            _ = os.environ.pop("PYTHONUNBUFFERED"
                               ) if "PYTHONUNBUFFERED" in os.environ else None

    @classmethod
    def print(cls, mode: str, text: str, ascii_art: bool = False, **kwargs):
        """print entry point

        :param mode: printing mode: std or standard, war or warning, err or error, inf or info, suc or success
        :param text: the text to be printed
        :param ascii_art: flag indicating if we print as an ascii-art or not
        :param kwargs: extra parameters to be passed to base cprint functions
        """
        # 1. transform mode to lowercase
        mode = mode.strip().lower()

        # 2. if not ascii-art mode, use the traditional methods to print the text
        if not ascii_art:
            if mode in ("std", "standard"):
                cls.std(text=text, **kwargs)
            elif mode in ("war", "warning"):
                cls.war(text=text, **kwargs)
            elif mode in ("err", "error"):
                cls.err(text=text, **kwargs)
            elif mode in ("inf", "info"):
                cls.info(text=text, **kwargs)
            elif mode in ("suc", "success"):
                cls.success(text=text, **kwargs)
        else:
            # 2.1 for ascii-art mode, compute the lines to be printed, then print the result
            lines = art.text2art(text)
            cls.print(mode=mode, text=lines, ascii_art=False, **kwargs)

    @classmethod
    def std(cls, text: str, end: str = '\n', **kwargs):
        """std: prints to stdout"""
        print(text, end=end, **kwargs)

    @classmethod
    def war(cls, text: str, end: str = '\n', **kwargs):
        """war: prints to stderr in yellow"""
        file = sys.stderr if kwargs.get("file") is None else None
        print(colorama.Fore.LIGHTYELLOW_EX + text,
              end=end,
              file=file,
              **kwargs)

    @classmethod
    def err(cls, text: str, end: str = '\n', **kwargs):
        """err: prints to stderr in red box"""
        file = sys.stderr if kwargs.get("file") is None else None
        print(colorama.Fore.YELLOW + colorama.Back.RED + text,
              end=end,
              file=file,
              **kwargs)

    @classmethod
    def info(cls, text: str, end: str = '\n', **kwargs):
        """info: prints to stderr in cyan"""
        file = sys.stderr if kwargs.get("file") is None else None
        print(colorama.Fore.LIGHTCYAN_EX + text, end=end, file=file, **kwargs)

    @classmethod
    def success(cls, text: str, end: str = '\n', **kwargs):
        """success: prints to stderr in green box"""
        file = sys.stderr if kwargs.get("file") is None else None
        print(colorama.Fore.BLACK + colorama.Back.GREEN + text,
              end=end,
              file=file,
              **kwargs)
