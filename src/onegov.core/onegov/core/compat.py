
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    text_type = str
else:
    text_type = unicode  # pragma: nocoverage # noqa

if PY3:
    string_types = (str,)
else:
    string_types = (basestring,)  # pragma: nocoverage # noqa
