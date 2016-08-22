import colorsys

from functools import lru_cache


def djb2_hash(text, size):
    """ Implementation of the djb2 hash, a simple hash function with a
    configurable table size.

    ** Do NOT use for cryptography! **

    """
    # arbitrary large prime number to initialize
    hash = 5381

    # hash(i) = hash(i-1) * 33 + str[i]
    for char in text:
        hash = ((hash << 5) + hash) + ord(char)

    # Output: integer between 0 and size-1 (inclusive)
    return hash % size


@lru_cache(maxsize=32)
def get_user_color(username):
    """ Gets a user color for each username which is used for the
    user-initials-* elements. Each username is mapped to a color.

    Since the colorspace is very limited there are lots of collisions.

    :returns: The user color in an css rgb string.

    """

    h = 100 / djb2_hash(username, 360)
    l = 0.9
    s = 0.5

    r, g, b = colorsys.hls_to_rgb(h, l, s)

    return '#{0:02x}{1:02x}{2:02x}'.format(
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255))
    )


def format_time_range(start, end):
    return correct_time_range('{:%H:%M} - {:%H:%M}'.format(start, end))


def correct_time_range(string):
    if string.endswith('00:00'):
        return string[:-5] + '24:00'
    return string
