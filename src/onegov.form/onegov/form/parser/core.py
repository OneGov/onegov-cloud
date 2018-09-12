""" onegov.form includes it's own markdownish form syntax, inspired by
https://github.com/maleldil/wmd

The goal of this syntax is to enable the creation of forms through the web,
without having to use javascript, html or python code.

Also, just like Markdown, we want this syntax to be readable by humans.

How it works
============

Internally, the form syntax is converted into a YAML file, which is in turn
parsed and turned into a WTForms class. We decided to go for the intermediate
YAML file because it's easy to define a Syntax which correctly supports
indentation. Our pyparsing approach was flimsy at best.

Parser Errors
=============

There's currently no sophisticated error check. It's possible that the parser
misunderstand something you defined without warning. So be careful to check
that what you wanted was actually what you got.

Syntax
======

Fields
------

Every field is identified by a label, an optional 'required' indicator and a
field definition. The Label can be any kind of text, not including ``*`` and
``=``.
The ``*`` indicates that a field is required. The ``=`` separates the
identifier from the definition.

A required field starts like this::

    My required field * =

An optional field starts like this::

    My optional field =

Following the identifier is the field definition. For example, this defines
a textfield::

    My textfield = ___

All possible fields are documented further below.

Fieldsets
---------

Fields are grouped into fieldsets. The fieldset of a field is the fieldset
that was last defined::

    # Fieldset 1
    I belong to Fieldset 1 = ___

    # Fieldset 2
    I belong to Fieldset 2 = ___

If no fieldset is defined, the fields don't belong to a fieldset. To stop
putting fields in a fieldset, define an empty fieldeset::

    # Fieldset 1
    I belong to Fieldset 1 = ___

    # ...
    I don't belong to a Fieldset = ___

Available Fields
----------------

Textfield
~~~~~~~~~

A textfield consists of exactly three underscores::

    I'm a textfield = ___

If the textfield is limited in length, the length can be given::

    I'm a limited textfield = ___[50]

The length of such textfields is validated.

Additionally, textfields may use regexes to validate their contents::

    I'm a numbers-only textfield = ___/^[0-9]+$

You *can* combine the length with a regex, though you probably don't want to::

    I'm a length-limited numbers-only textfield = ___[4]/^[0-9]+$

This could be simplified as follows:

    I'm a length-limited numbers-only textfield = ___/^[0-9]{0,4}$

Note that you don't *need* to specify the beginning (^) and the end ($) of the
string, but not doing so might result in unexpected results. For example,
while '123abc' is invalid for ``___/^[0-9]+$``, it is perfectly valid for
``___/[0-9]+``. The latter only demands that the text starts with a number,
not that it only consists of numbers!

Textarea
~~~~~~~~

A textarea has no limit and consists of exactly three dots::

    I'm a textarea = ...

Optionally, the number of rows can be passed to the field. This changes the
way the textarea looks, not the way it acts::

    I'm a textarea with 10 rows = ...[10]

Password
~~~~~~~~

A password field consists of exactly three stars::

    I'm a password = ***

E-Mail
~~~~~~

An e-mail field consists of exactly three ``@``::

    I'm an e-mail field = @@@


URL
~~~

An url field consists of the http/https prefix::

    I'm an url field = http://
    I'm the exact same = https://

Whether or not you enter http or https has no bearing on the validation.

Date
~~~~

A date (without time) is defined by this exact string: ``YYYY.MM.DD``::

    I'm a date field = YYYY.MM.DD

Note that this doesn't mean that the date format can be influenced.

Datetime
~~~~~~~~

A date (with time) is defined by this exact string: ``YYYY.MM.DD HH:MM``::

    I'm a datetime field = YYYY.MM.DD HH:MM

Again, this doesn't mean that the datetime format can be influenced.

Time
~~~~

A Time is defined by this exact string: ``HH:MM``::

    I'm a time field = HH:MM

One more time, this doesn't mean that the datetime format can be influenced.

Numbers
~~~~~~~

There are two types of number fields. An integer and a float field::

    I'm an integer field = 0..99
    I'm an integer field of a different range = -100..100

    I'm a float field = 0.00..99.00
    I'm an float field of a different range = -100.00..100.00

Code
~~~~

To write code in a certain syntax, use the following::

    Description = <markdown>

Currently, only markdown is supported.

Files
~~~~~

A file upload is defined like this::

    I'm a file upload field = *.*

This particular example would allow any file. To allow only certain files
do something like this::

    I'm a image filed = *.png|*.jpg|*.gif
    I'm a document = *.doc
    I'm any document = *.doc|*.pdf

The files are checked against their file extension. Onegov.form also checks
that uploaded files have the mimetype they claim to have and it won't accept
obviously dangerous uploads like binaries (unless you really want to).

Standard Numbers
~~~~~~~~~~~~~~~~

onegov.form uses `python-stdnum \
<https://github.com/arthurdejong/python-stdnum>`_ to offer a wide range of
standard formats that are guaranteed to be validated.

To use, simply use a `#`, followed by the stdnum format to use::

    I'm a valid IBAN (or empty) = # iban
    I'm a valid IBAN (required) * = # iban

The format string after the `#` must be importable from stdnum. In other words,
this must work, if you are using ``ch.ssn`` (to use an example)::

    $ python
    >>> from stdnum.ch import ssn

This is a bit of an advanced feature and since it delegates most work to an
external library there's no guarantee that a format once used may be reused
in the future.

Still, the library should be somewhat stable and the benefit is huge.

To see the available format, have a look at the docs:
`<http://arthurdejong.org/python-stdnum/doc/1.1/index.html#available-formats>`_

Radio Buttons
~~~~~~~~~~~~~

Radio button fields consist of x radio buttons, out of which one may be
preselected. Radio buttons need to be indented on the lines after the
definition::

    Gender =
        ( ) Female
        ( ) Male
        (x) I don't want to say

Radio buttons also have the ability to define optional form parts. Those
parts are only shown if a question was answered a certain way.

Form parts are properly nested if they lign up with the label above them.

For example::

    Delivery Method =
        ( ) Pickup
            Pickup Time * = ___
        (x) Address
            Street * = ___
            Town * = ___

Here, the street and the town only need to be provided, if the delivery method
is 'Address'. If the user selects a different option, the fields are not
shown and they will not be required.

On the other hand, if 'Pickup' is selected, the 'Pickup Time' needs to be
filled out and the address options are hidden.

This kind of nesting may continue ad infinitum. Meaning you can nest radio
buttons as deeply as you like. Note however, that this is discouraged and that
your users will not be too happy if you present them with a deeply nested
form.

More than one level of nesting is a clear indicator that your form is too
complex.

Checkboxes
~~~~~~~~~~

Checkboxes work exactly like radio buttons, just that you can select
multiple fields::

    Extras =
        [x] Phone insurance
        [ ] Phone case
        [x] Extra battery

Just like radiobuttons, checkboxes may be nested to created dependencies::

    Additional toppings =
        [ ] Salami
        [ ] Olives
        [ ] Other
            Description = ___

Pricing Information
~~~~~~~~~~~~~~~~~~~

Radio buttons and checkboxes may be priced. For example, the following order
form can be modeled::

    Node Size =
        ( ) Small (20 USD)
        (x) Medium (30 USD)
        ( ) Large (40 USD)

    Extras =
        [x] Second IP Address (20 CHF)
        [x] Backup (20 CHF)

The additional pricing metadata can be used to provide simple order forms.
As in any other form, dependencies are taken into account.

"""

import pyparsing as pp
import re
import yaml

from cached_property import cached_property
from dateutil import parser as dateutil_parser
from decimal import Decimal
from onegov.core.utils import Bunch
from onegov.form import errors
from onegov.form.parser.grammar import checkbox
from onegov.form.parser.grammar import code
from onegov.form.parser.grammar import date
from onegov.form.parser.grammar import datetime
from onegov.form.parser.grammar import decimal_range_field
from onegov.form.parser.grammar import email
from onegov.form.parser.grammar import field_identifier
from onegov.form.parser.grammar import fieldset_title
from onegov.form.parser.grammar import fileinput
from onegov.form.parser.grammar import integer_range_field
from onegov.form.parser.grammar import password
from onegov.form.parser.grammar import radio
from onegov.form.parser.grammar import stdnum
from onegov.form.parser.grammar import textarea
from onegov.form.parser.grammar import textfield
from onegov.form.parser.grammar import time
from onegov.form.parser.grammar import url
from onegov.form.utils import as_internal_id


# cache the parser elements
def create_parser_elements():
    elements = Bunch()
    elements.identifier = field_identifier()
    elements.fieldset_title = fieldset_title()
    elements.textfield = textfield()
    elements.textarea = textarea()
    elements.code = code()
    elements.password = password()
    elements.email = email()
    elements.url = url()
    elements.stdnum = stdnum()
    elements.datetime = datetime()
    elements.date = date()
    elements.time = time()
    elements.fileinput = fileinput()
    elements.radio = radio()
    elements.checkbox = checkbox()
    elements.integer_range = integer_range_field()
    elements.decimal_range = decimal_range_field()
    elements.boxes = elements.checkbox | elements.radio
    elements.single_line_fields = elements.identifier + pp.MatchFirst([
        elements.textfield,
        elements.textarea,
        elements.code,
        elements.password,
        elements.email,
        elements.url,
        elements.stdnum,
        elements.datetime,
        elements.date,
        elements.time,
        elements.fileinput,
        elements.integer_range,
        elements.decimal_range,
    ])

    return elements


ELEMENTS = create_parser_elements()


class CustomLoader(yaml.SafeLoader):
    """ Extends the default yaml loader with customized constructors. """


class constructor(object):
    """ Adds decorated functions to as constructors to the CustomLoader. """

    def __init__(self, tag):
        self.tag = tag

    def __call__(self, fn):
        CustomLoader.add_constructor(self.tag, fn)
        return fn


@constructor('!text')
def construct_textfield(loader, node):
    return ELEMENTS.textfield.parseString(node.value)


@constructor('!textarea')
def construct_textarea(loader, node):
    return ELEMENTS.textarea.parseString(node.value)


@constructor('!code')
def construct_syntax(loader, node):
    return ELEMENTS.code.parseString(node.value)


@constructor('!email')
def construct_email(loader, node):
    return ELEMENTS.email.parseString(node.value)


@constructor('!url')
def construct_url(loader, node):
    return ELEMENTS.url.parseString(node.value)


@constructor('!stdnum')
def construct_stdnum(loader, node):
    return ELEMENTS.stdnum.parseString(node.value)


@constructor('!date')
def construct_date(loader, node):
    return ELEMENTS.date.parseString(node.value)


@constructor('!datetime')
def construct_datetime(loader, node):
    return ELEMENTS.datetime.parseString(node.value)


@constructor('!time')
def construct_time(loader, node):
    return ELEMENTS.time.parseString(node.value)


@constructor('!radio')
def construct_radio(loader, node):
    return ELEMENTS.radio.parseString(node.value)


@constructor('!checkbox')
def construct_checkbox(loader, node):
    return ELEMENTS.checkbox.parseString(node.value)


@constructor('!fileinput')
def construct_fileinput(loader, node):
    return ELEMENTS.fileinput.parseString(node.value)


@constructor('!password')
def construct_password(loader, node):
    return ELEMENTS.password.parseString(node.value)


@constructor('!decimal_range')
def construct_decimal_range(loader, node):
    return ELEMENTS.decimal_range.parseString(node.value)


@constructor('!integer_range')
def construct_integer_range(loader, node):
    return ELEMENTS.integer_range.parseString(node.value)


def flatten_fieldsets(fieldsets):
    for fieldset in fieldsets:
        yield from flatten_fields(fieldset.fields)


def flatten_fields(fields):
    fields = fields or []

    for field in fields:
        yield field

        if hasattr(field, 'fields'):
            yield from flatten_fields(field.fields)

        if hasattr(field, 'choices'):
            for choice in field.choices:
                yield from flatten_fields(choice.fields)


def find_field(fieldsets, id):
    id = as_internal_id(id or '')

    for fieldset in fieldsets:
        if fieldset.id == id:
            return fieldset

        if not fieldset.id or id.startswith(fieldset.id):
            for field in flatten_fields(fieldset.fields):
                if field.id == id:
                    return field


class Fieldset(object):
    """ Represents a parsed fieldset. """

    def __init__(self, label, fields=None):
        self.label = label if label != '...' else None
        self.fields = fields or []

    @property
    def id(self):
        return as_internal_id(self.human_id)

    @property
    def human_id(self):
        return self.label or ''

    def find_field(self, *args, **kwargs):
        return find_field((self, ), *args, **kwargs)


class Choice(object):
    """ Represents a parsed choice.

    Note: Choices may have child-fields which are meant to be shown to the
    user if the given choice was selected.

    """
    def __init__(self, key, label, selected=False, fields=None):
        self.key = key
        self.label = label
        self.selected = selected
        self.fields = fields


class Field(object):
    """ Represents a parsed field. """

    def __init__(self, label, required, parent=None, fieldset=None, **kwargs):
        self.label = label
        self.required = required
        self.parent = parent
        self.fieldset = fieldset

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def id(self):
        return as_internal_id(self.human_id)

    @cached_property
    def human_id(self):
        if self.parent:
            return '/'.join((
                self.parent.human_id,
                self.label
            ))

        if self.fieldset.human_id:
            return '/'.join((
                self.fieldset.human_id,
                self.label
            ))

        return self.label

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset
        )

    def parse(self, value):
        return value


class PasswordField(Field):
    type = 'password'


class EmailField(Field):
    type = 'email'


class UrlField(Field):
    type = 'url'


class DateField(Field):
    type = 'date'

    def parse(self, value):
        # the first int in an ambiguous date is assumed to be a day
        # (since our software runs in europe first and foremost)
        return dateutil_parser.parse(value, dayfirst=True).date()


class DatetimeField(Field):
    type = 'datetime'

    def parse(self, value):
        # the first int in an ambiguous date is assumed to be a day
        # (since our software runs in europe first and foremost)
        return dateutil_parser.parse(value, dayfirst=True)


class TimeField(Field):
    type = 'time'

    def parse(self, value):
        return time(*map(int, value.split(':')))


class TextField(Field):
    type = 'text'

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        regex = field.regex and re.compile(field.regex) or None

        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            maxlength=field.length or None,
            regex=regex
        )


class TextAreaField(Field):
    type = 'textarea'

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            rows=field.rows or None
        )


class CodeField(Field):
    type = 'code'

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            syntax=field.syntax
        )


class StdnumField(Field):
    type = 'stdnum'

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            format=field.format
        )


class RangeField(object):

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            range=field[0]
        )


class IntegerRangeField(RangeField, Field):
    type = 'integer_range'

    def parse(self, value):
        return int(float(value))  # automatically truncates dots


class DecimalRangeField(RangeField, Field):
    type = 'decimal_range'

    def parse(self, value):
        return Decimal(value)


class FileinputField(Field):
    type = 'fileinput'

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            extensions=field.extensions
        )


class OptionsField(object):

    @classmethod
    def create(cls, field, identifier, parent=None, fieldset=None):
        choices = [
            Choice(
                key=c.label,
                label=c.label + format_pricing(c.pricing),
                selected=c.checked
            )
            for c in field.choices
        ]

        pricing = {c.label: c.pricing for c in field.choices if c.pricing}

        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            choices=choices,
            pricing=pricing or None
        )

    def parse(self, value):
        if isinstance(value, str):
            return [v.strip() for v in value.split('\n')]

        return value


class RadioField(OptionsField, Field):
    type = 'radio'

    def parse(self, value):
        v = super().parse(value)
        return v and v[0] or None


class CheckboxField(OptionsField, Field):
    type = 'checkbox'


def parse_formcode(formcode):
    """ Takes the given formcode and returns an intermediate representation
    that can be used to generate forms or do other things.

    """
    parsed = yaml.load('\n'.join(translate_to_yaml(formcode)), CustomLoader)

    fieldsets = []
    field_classes = {cls.type: cls for cls in Field.__subclasses__()}
    used_ids = set()

    for fieldset in parsed:

        # fieldsets occur only at the top level
        label = next(k for k in fieldset.keys())
        fs = Fieldset(label)

        fs.fields = [
            parse_field_block(block, field_classes, used_ids, fs)
            for block in fieldset[label]
        ]

        fieldsets.append(fs)

    return fieldsets


def parse_field_block(field_block, field_classes,
                      used_ids, fieldset, parent=None):
    """ Takes the given parsed field block and yields the fields from it """

    key, field = next(i for i in field_block.items())

    identifier_src = key.rstrip('= ') + '='
    identifier = ELEMENTS.identifier.parseString(identifier_src)

    # add the nested options/dependencies in case of radio/checkbox buttons
    if isinstance(field, list):
        choices = [next(i for i in f.items()) for f in field]

        for choice, dependencies in choices:
            choice.dependencies = dependencies

        choices = [c[0] for c in choices]

        field = Bunch(choices=choices, type=choices[0].type)

        # make sure only one type is found (either radio or checkbox)
        types = {f.type for f in field.choices}
        assert types <= {'radio', 'checkbox'}
        assert len(types) == 1

    result = field_classes[field.type].create(
        field, identifier, parent, fieldset)

    if result.id in used_ids:
        raise errors.DuplicateLabelError(label=result.label)

    used_ids.add(result.id)

    # go through nested blocks and recursively add them
    if field.type in {'radio', 'checkbox'}:
        for ix, choice in enumerate(field.choices):
            if not choice.dependencies:
                continue

            result.choices[ix].fields = [
                parse_field_block(
                    field_block=child,
                    field_classes=field_classes,
                    used_ids=used_ids,
                    fieldset=fieldset,
                    parent=result
                )
                for child in choice.dependencies
            ]

    return result


def format_pricing(pricing):
    if not pricing:
        return ''

    return ' ({:.2f} {})'.format(pricing[0], pricing[1])


def match(expr, text):
    """ Returns true if the given parser expression matches the given text. """
    try:
        expr.parseString(text)
    except pp.ParseException:
        return False
    else:
        return True


def try_parse(expr, text):
    """ Returns the result of the given parser expression and text, or None.

    """
    try:
        return expr.parseString(text)
    except pp.ParseException:
        return None


def prepare(text):
    """ Takes the raw form source and prepares it for the translation into
    yaml.

    """

    lines = (l.rstrip() for l in text.split('\n'))
    lines = ((ix, l) for ix, l in enumerate(lines) if l)
    lines = ((ix, l) for ix, l in ensure_a_fieldset(lines))

    for line in lines:
        yield line


def ensure_a_fieldset(lines):
    """ Makes sure that the given lines all belong to a fieldset. That means
    adding an empty fieldset before all lines, if none is found first.

    """
    found_fieldset = False

    for ix, line in lines:
        if found_fieldset:
            yield ix, line
            continue

        if match(ELEMENTS.fieldset_title, line):
            found_fieldset = True
            yield ix, line
        else:
            found_fieldset = True
            yield -1, '# ...'
            yield ix, line


def translate_to_yaml(text):
    """ Takes the given form text and constructs an easier to parse yaml
    string.

    """

    lines = ((ix, l) for ix, l in prepare(text))
    expect_nested = False
    actual_fields = 0
    ix = 0

    def escape_single(text):
        return text.replace("'", "''")

    def escape_double(text):
        return text.replace('"', '\\"')

    for ix, line in lines:

        indent = ' ' * (4 + (len(line) - len(line.lstrip())))

        # the top level are the fieldsets
        if match(ELEMENTS.fieldset_title, line):
            yield '- "{}":'.format(escape_double(line.lstrip('# ').rstrip()))
            expect_nested = False
            continue

        # fields are nested lists of dictionaries
        try:
            parse_result = try_parse(ELEMENTS.single_line_fields, line)
        except re.error:
            raise errors.InvalidFormSyntax(line=ix + 1)

        if parse_result is not None:
            yield '{indent}- "{identifier}": !{type} \'{definition}\''.format(
                indent=indent,
                type=parse_result.type,
                identifier=escape_double(line.split('=')[0].strip()),
                definition=escape_single(line.split('=')[1].strip())
            )
            expect_nested = len(indent) > 4
            actual_fields += 1
            continue

        # checkboxes/radios come without identifier
        parse_result = try_parse(ELEMENTS.boxes, line)
        if parse_result is not None:

            if not expect_nested:
                raise errors.InvalidFormSyntax(line=ix + 1)

            yield '{indent}- !{type} \'{definition}\':'.format(
                indent=indent,
                type=parse_result.type,
                definition=escape_single(line.strip())
            )
            continue

        # identifiers which are alone contain nested checkboxes/radios
        if match(ELEMENTS.identifier, line):

            # this should have been matched by the single line field above
            if not line.endswith('='):
                raise errors.InvalidFormSyntax(line=ix + 1)

            yield '{indent}- "{identifier}":'.format(
                indent=indent,
                identifier=escape_double(line.strip())
            )

            expect_nested = True
            actual_fields += 1
            continue

        raise errors.InvalidFormSyntax(line=ix + 1)

    if not actual_fields:
        raise errors.InvalidFormSyntax(line=ix + 1)
