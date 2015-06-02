import itertools
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

if PY3:
    zip_longest = itertools.zip_longest
else:
    zip_longest = itertools.izip_longest  # pragma: nocoverage # noqa

if PY3:
    from io import StringIO, BytesIO
else:
    from cStringIO import StringIO  # pragma: nocoverage # noqa
    BytesIO = StringIO  # pragma: nocoverage # noqa
