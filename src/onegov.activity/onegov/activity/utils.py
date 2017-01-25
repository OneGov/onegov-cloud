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


def generate_checksum(number):
    """ Generates the modulo 10 checksum as required by Postfinance.

    :return: The checksum as integer.

    """

    table = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5)
    carry = 0

    for n in str(number):
        carry = table[(carry + int(n)) % 10]

    return (10 - carry) % 10


def append_checksum(number):
    """ Adds the Postfinance modulo 10 checksum to the given number.

    :return: The given number as string with the checksum appended.

    """
    number = str(number)
    return number + str(generate_checksum(number))


def is_valid_checksum(number):
    """ Takes the given number and verifys the checksum which is assumed to
    be the last digit in the given number.

    :return: True if the checksum digit matches the numbers before it.

    """

    number = str(number)
    return number[-1] == str(generate_checksum(number[:-1]))
