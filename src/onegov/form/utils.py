import re
import wtforms.widgets.core

from decimal import Decimal
from hashlib import md5
from unidecode import unidecode

_unwanted_characters = re.compile(r'[^a-zA-Z0-9]+')
_html_tags = re.compile(r'<.*?>')

original_html_params = wtforms.widgets.core.html_params


def as_internal_id(label):
    clean = unidecode(label).strip(' \"\'').lower()
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


def disable_required_attribute_in_html_inputs():
    """ Replaces the required attribute with aria-required. """

    def patched_html_params(**kwargs):
        if kwargs.pop('required', None):
            kwargs['aria_required'] = True
        return original_html_params(**kwargs)

    wtforms.widgets.core.html_params = patched_html_params
    wtforms.widgets.core.Input.html_params = staticmethod(patched_html_params)


class decimal_range:
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


def hash_definition(definition):
    return md5(definition.encode('utf-8')).hexdigest()


def path_to_filename(path):
    if not path:
        return
    if not isinstance(path, str):
        raise ValueError
    if '/' in path:
        return path.split('/')[-1]
    if '\\' in path:
        return path.split('\\')[-1]
    return path
