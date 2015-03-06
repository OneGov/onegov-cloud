import re


number_suffix = re.compile(r'-([0-9]+)$')


def increment_name(name):
    """ Takes the given name and adds a numbered suffix beginning at 1.

    For example::

        foo => foo-1
        foo-1 => foo-2

    """

    match = number_suffix.search(name)
    number = (match and int(match.group(1)) or 0) + 1

    if match:
        return number_suffix.sub('-{}'.format(number), name)
    else:
        return name + '-{}'.format(number)
