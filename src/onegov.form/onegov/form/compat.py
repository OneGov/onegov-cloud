import sys

PY3 = sys.version_info[0] == 3


if PY3:
    unicode_characters = ''.join(
        chr(c) for c in range(65536) if not chr(c).isspace())
else:
    # pragma: nocoverage
    unicode_characters = ''.join(
        unichr(c) for c in xrange(65536) if not unichr(c).isspace())  # noqa
