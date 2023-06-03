"""split range function"""


def split_range(n: int, parts: int) -> list[tuple[int, int]]:
    """split the interval from [0,n) = [0, 1, 2, ..., n-2, n-1]
     of size `n` in `parts` parts of quasi equal size.

    useful when try to read files in parallel or compute a large
    list in chunks of quasi-equal size.

    ===============

    let m = parts
    then
        n = m * s + r
    where s is the chunk size and r is the remainder.
    In general, we have two split parts,
    i: r intervals of size s+1
    ii: (m-r) intervals of size s

    i:  from k*(s+1) to (k+1)*(s+1)          , for 0 <= k < r
    ii: from r*(s+1)+a*s to r*(s+1)+(a+1)*s  , for 0 <= a < m - r


    :param n: the interval size
    :param parts: number of parts>=1
    :return: the list with split intervals
    """

    if parts < 1 or n < 1:
        raise ValueError(
            f"split_range(n,parts) expects n>=1 and parts>=1. Values provided n={n}, parts={parts}"
        )

    m = parts
    s = n // parts
    r = n % parts

    batch_sizes_block_1 = [(k * (s + 1), (k + 1) * (s + 1)) for k in range(r)]
    batch_sizes_block_2 = [(r * (s + 1) + a * s, r * (s + 1) + (a + 1) * s)
                           for a in range(m - r)]

    batch_sizes = batch_sizes_block_1 + batch_sizes_block_2
    return batch_sizes


def split_range_ab(a: int, b: int, parts: int) -> list[tuple[int, int]]:
    """split interval [a,b) in `parts` parts"""
    # 1. compute the base interval
    n = b - a
    base_intervals = split_range(n, parts)
    # 2. adjust the base interval to the given interval [a,b)
    intervals = [(a + i, a + j) for i, j in base_intervals]

    return intervals
