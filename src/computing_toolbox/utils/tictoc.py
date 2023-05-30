"""Computes elapsed times using classical function `tic` and `toc` from matlkab world"""
import logging
import time
from collections import defaultdict

# configure logging with INFO level to show verbose messages
logging.basicConfig(level=logging.INFO)
# define global dictionaries
tictoc_dict = defaultdict(float)
t0_verbose_dict = defaultdict(bool)


def tic(key: str = "__DEFAULT__", verbose: bool = False):
    """start timer with the `key` and track verbose mode"""
    t0 = time.perf_counter()
    tictoc_dict[key] = t0
    t0_verbose_dict[key] = verbose
    if verbose:
        message = f"Begin timer [{key}]: {t0}"
        logging.info(message)


def toc(key: str = "__DEFAULT__", verbose: bool = True) -> float:
    """stop timer with `key` and if tic was verbose: print the equivalent message here"""
    t1 = time.perf_counter()
    t0 = tictoc_dict[key]
    elapsed = t1 - t0
    if t0_verbose_dict[key]:
        message = f"End timer [{key}]: {t0}"
        logging.info(message)
    if verbose:
        message = f"Elapsed time [{key}]: {elapsed} seconds"
        logging.info(message)
    return elapsed
