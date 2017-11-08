import re

from decimal import Decimal
from unidecode import unidecode

_unwanted_characters = re.compile(r'[^a-zA-Z0-9]+')
_html_tags = re.compile(r'<.*?>')


def as_internal_id(label):
    clean = unidecode(label).strip(' ').lower()
    clean = _unwanted_characters.sub('_', clean)

    return clean


def get_fields_from_class(cls):
    fields = []

    for name in dir(cls):
        if not name.startswith('_'):
            field = getattr(cls, name)

            if hasattr(field, '_formfield'):
                fields.append((name, field))

    fields.sort(key=lambda x: (x[1].creation_counter, x[0]))

    return fields


def extract_text_from_html(html):
    return _html_tags.sub('', html)


class decimal_range(object):
    """ Implementation of Python's range builtin using decimal values instead
    of integers.

    """

    def __init__(self, start, stop, step=None):
        if step is None and start <= stop:
            step = '1.0'
        elif step is None and start >= stop:
            step = '-1.0'

        self.start = self.current = Decimal(start)
        self.stop = Decimal(stop)
        self.step = Decimal(step)

        assert self.step != Decimal('0')

    def __repr__(self):
        if self.start <= self.stop and self.step == Decimal('1.0'):
            return "decimal_range('{}', '{}')".format(self.start, self.stop)
        elif self.start >= self.stop and self.step == Decimal('-1.0'):
            return "decimal_range('{}', '{}')".format(self.start, self.stop)
        else:
            return "decimal_range('{}', '{}', '{}')".format(
                self.start, self.stop, self.step
            )

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return (self.start, self.stop, self.step)\
            == (other.start, other.stop, other.step)

    def __iter__(self):
        return self

    def __next__(self):
        result, self.current = self.current, self.current + self.step

        if self.step > 0 and result >= self.stop:
            raise StopIteration

        if self.step < 0 and result <= self.stop:
            raise StopIteration

        return result
