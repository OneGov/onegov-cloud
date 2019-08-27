import inspect
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


def use_required_attribute_in_html_inputs(use):
    used = wtforms.widgets.core.html_params is original_html_params

    if use == used:
        return

    if use:
        function = original_html_params
    else:
        def patched_html_params(**kwargs):
            kwargs.pop('required', None)
            return original_html_params(**kwargs)

        function = patched_html_params

    wtforms.widgets.core.html_params = function
    wtforms.widgets.core.Input.html_params = staticmethod(function)


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


def hash_definition(definition):
    return md5(definition.encode('utf-8')).hexdigest()


def with_options(widget, **render_options):
    """ Takes a widget class or instance and returns a child-instance of the
    widget class, with the given options set on the render call.

    This makes it easy to use existing WTForms widgets with custom render
    options:

    field = StringField(widget=with_options(TextArea, class_="markdown"))

    Note: With wtforms 2.1 this is no longer necssary. Instead use the
    render_kw parameter of the field class. This function will be deprecated
    in a future release.

    """

    if inspect.isclass(widget):
        class Widget(widget):

            def __call__(self, *args, **kwargs):
                render_options.update(kwargs)
                return super().__call__(*args, **render_options)

        return Widget()
    else:
        class Widget(widget.__class__):

            def __init__(self):
                self.__dict__.update(widget.__dict__)

            def __call__(self, *args, **kwargs):
                render_options.update(kwargs)
                return widget.__call__(*args, **render_options)

        return Widget()
