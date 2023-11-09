"""list recursively given the root dir"""
import os
import re
from itertools import count

from typing import Generator

from tqdm import tqdm


class Lsr:
    """the lsr class"""

    def __init__(self,
                 root: str,
                 re_filter: str = r".*",
                 re_kwargs: dict or None = None):
        """mimic the `ls -r` but applying a regex filter

        :param root: the root directory
        :param re_filter: the regular expression to be filtered
        :param re_kwargs: extra parameters for re.compile
        :return: a generator that generates the paths matching the re filter
        """
        self.root = root
        self.re_filter = re_filter
        self.re_kwargs = re_kwargs if re_kwargs else {}

        self.total = 0
        self.success = 0

    def run(self, pbar: tqdm or None = None) -> Generator:
        """run the ls -r command"""
        regex = re.compile(self.re_filter, **self.re_kwargs)

        self.total = 0
        self.success = 0
        # 1. walk over the directories
        for dirpath, dirnames, filenames in os.walk(self.root):
            # 2. walk over the dirnames and then over the filenames
            for path_i in (dirnames, filenames):
                # 2.1 walk over the path_i
                for path_ij in path_i:
                    self.total += 1
                    _ = pbar.update() if pbar else None
                    # 2.1.1 build the full path
                    path = os.path.join(dirpath, path_ij)
                    # 2.1.2 yield it if match
                    if regex.findall(path):
                        self.success += 1
                        _ = pbar.set_postfix_str(
                            f"#SUCCESS:🟢{self.success}/{self.total}"
                        ) if pbar else None
                        yield path


def lsr(root: str,
        re_filter: str = r".*",
        re_kwargs: dict or None = None,
        tqdm_kwargs: dict or None = None) -> Generator:
    """wrapper for Lsr(***).run()"""
    # 1. instantiate the Lsr object
    lister = Lsr(root=root, re_filter=re_filter, re_kwargs=re_kwargs)
    # 2. build the pbar with their parameters or set it to None
    kwargs = {
        "desc": f"listing files in '{root}'",
        **tqdm_kwargs
    } if tqdm_kwargs is not None else None
    pbar = tqdm(count(), **kwargs) if kwargs is not None else None
    # 3. return the generator object
    return lister.run(pbar=pbar)
