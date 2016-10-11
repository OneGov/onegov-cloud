import string

from random import SystemRandom


GROUP_CODE_CHARS = string.ascii_uppercase + string.digits
GROUP_CODE_LENGTH = 10


def random_group_code():
    random = SystemRandom()

    return ''.join(
        random.choice(GROUP_CODE_CHARS)
        for _ in range(GROUP_CODE_LENGTH)
    )


def overlaps(range_a, range_b):
    return range_b[0] <= range_a[0] and range_a[0] <= range_b[1] or\
        range_a[0] <= range_b[0] and range_b[0] <= range_a[1]


def merge_ranges(ranges):
    """ Merges the given list of ranges into a list of ranges including only
    exclusive ranges. The ranges are turned into tuples to make them
    hashable.

    """

    ranges = sorted(list(ranges))

    # stack of merged values
    merged = [tuple(ranges[0])]

    for r in ranges:
        if overlaps(merged[-1], r):
            merged[-1] = (merged[-1][0], r[1])
        else:
            merged.append(tuple(r))

    return merged
