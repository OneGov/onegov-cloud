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

Comments can be added beneath a field, using the same indentation::

    My textfield = ___
    << Explanation for my field >>

All characters are allowed except ''>''.

Complex example::

    Delivery * =
        (x) I want it delivered
            Alternate Address =
                (x) No
                ( ) Yes
                    Street = ___
                    << street >>
                    Town = ___
            << Alt >>
        ( ) I want to pick it up
    << delivery >>

    Kommentar = ...
    << kommentar >>

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

Video Link
~~~~~~~~~~

An url field pointing to a video ``video-url``::

    I' am a video link = video-url

In case of vimeo or youtube videos the video will be embedded in the page,
otherwise the link will be shown.


Date
~~~~

A date (without time) is defined by this exact string: ``YYYY.MM.DD``::

    I'm a date field = YYYY.MM.DD

Note that this doesn't mean that the date format can be influenced.

A date field optionally can be limited to a relative or absolute date range.
Note that the edges of the interval are inclusive. The list of possible
grains for relative dates are ``years``, ``months``, ``weeks`` and ``days``
as well as the special value ``today``.

    I'm a future date field = YYYY.MM.DD (+1 days..)
    I'm on today or in the future = YYYY.MM.DD (today..)
    At least two weeks ago = YYYY.MM.DD (..-2 weeks)
    Between 2010 and 2020 = YYYY.MM.DD (2010.01.01..2020.12.31)

Datetime
~~~~~~~~

A date (with time) is defined by this exact string: ``YYYY.MM.DD HH:MM``::

    I'm a datetime field = YYYY.MM.DD HH:MM
    I'm a futue datetime field = YYYY.MM.DD HH:MM (today..)

Again, this doesn't mean that the datetime format can be influenced.

The same range validation that can be applied to date fields can also be
applied to datetime. Note however that the Validation will be applied to
to the date portion. The time portion is ignored completely.

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

Integer fields optionally can have a price attached to them which will be
multiplied by the supplied integer::

    Number of stamps to include = 0..30 (1.00 CHF)

This will result in a price of 1.00 CHF per stamp.

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

These file inputs allow only for one file to be uploaded. If you want to
allow multiple files to be uploaded, use the following syntax::

    I'm a multiple file upload field = *.* (multiple)

This will allow the user to upload multiple files at once.

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
`<https://arthurdejong.org/python-stdnum/doc/1.1/index.html#available-formats>`_

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

    Delivery =
        (x) Pickup (0 CHF)
        ( ) Delivery (5 CHF!)

The additional pricing metadata can be used to provide simple order forms.
As in any other form, dependencies are taken into account.

The optional `!` at the end of the price indicates that credit card payment
will become mandatory if this option is selected. It is possible to achieve
this without a price increase too: (0 CHF!)

Discounts
~~~~~~~~~

Radio buttons and checkboxes may apply proportial discounts. How those
discounts are applied will depend on the consumer. It will not be factored
into the price of the form automatically, since there may be other costs
associated with the submission, that aren't part of the form.

Example discount::

    Discount =
        (x) No discount
        ( ) Sports club (50%)
        ( ) School (100%)

"""
from __future__ import annotations

import pyparsing as pp
import re
import yaml

from functools import cached_property
from dateutil import parser as dateutil_parser
from decimal import Decimal
from functools import lru_cache
from onegov.core.utils import Bunch
from onegov.form import errors
from onegov.form.parser.grammar import checkbox, chip_nr, field_help_identifier
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
from onegov.form.parser.grammar import video_url
from onegov.form.utils import as_internal_id


from typing import final, Any, ClassVar, Literal, Self, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from onegov.form.types import PricingRules
    from onegov.form.utils import decimal_range
    from pyparsing import ParseResults
    from re import Pattern
    from typing import TypeAlias
    from yaml.nodes import ScalarNode

    # tagged unions so we can type narrow by type field
    BasicParsedField: TypeAlias = (
        'PasswordField | EmailField | UrlField | VideoURLField | DateField | '
        'DatetimeField | TimeField | StringField | TextAreaField | '
        'CodeField | StdnumField | IntegerRangeField | '
        'DecimalRangeField | RadioField | CheckboxField | ChipNrField'
    )
    FileParsedField: TypeAlias = 'FileinputField | MultipleFileinputField'
    ParsedField: TypeAlias = BasicParsedField | FileParsedField

_FieldT = TypeVar('_FieldT', bound='ParsedField')


# cache the parser elements
def create_parser_elements() -> Bunch:
    elements = Bunch()
    elements.identifier = field_identifier()
    elements.help_identifier = field_help_identifier()
    elements.fieldset_title = fieldset_title()
    elements.textfield = textfield()
    elements.textarea = textarea()
    elements.code = code()
    elements.password = password()
    elements.email = email()
    elements.url = url()
    elements.video_url = video_url()
    elements.stdnum = stdnum()
    elements.datetime = datetime()
    elements.date = date()
    elements.time = time()
    elements.fileinput = fileinput()
    elements.multiplefileinput = fileinput()
    elements.radio = radio()
    elements.checkbox = checkbox()
    elements.integer_range = integer_range_field()
    elements.decimal_range = decimal_range_field()
    elements.chip_nr = chip_nr()
    elements.boxes = elements.checkbox | elements.radio
    elements.single_line_fields = elements.identifier + pp.MatchFirst([
        elements.textfield,
        elements.textarea,
        elements.code,
        elements.password,
        elements.email,
        elements.url,
        elements.video_url,
        elements.stdnum,
        elements.datetime,
        elements.date,
        elements.time,
        elements.fileinput,
        elements.integer_range,
        elements.decimal_range,
        elements.chip_nr,
    ])

    return elements


# lazy loads the parser elements and stores them as attributes on itself
class LazyElements:

    def __init__(self) -> None:
        self.loaded = False

    def __getattr__(self, name: str) -> pp.ParserElement:
        if not self.loaded:
            for k, v in create_parser_elements().__dict__.items():
                setattr(self, k, v)

            self.loaded = True

        if name in self.__dict__:
            return self.__dict__[name]

        raise AttributeError(name)


ELEMENTS = LazyElements()


class CustomLoader(yaml.SafeLoader):
    """ Extends the default yaml loader with customized constructors. """


class constructor:  # noqa: N801
    """ Adds decorated functions to as constructors to the CustomLoader. """

    def __init__(self, tag: str):
        self.tag = tag

    def __call__(
        self,
        fn: Callable[[CustomLoader, ScalarNode], pp.ParseResults]
    ) -> Callable[[CustomLoader, ScalarNode], pp.ParseResults]:
        CustomLoader.add_constructor(self.tag, fn)
        return fn


@constructor('!text')
def construct_textfield(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.textfield.parse_string(node.value)


@constructor('!textarea')
def construct_textarea(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.textarea.parse_string(node.value)


@constructor('!code')
def construct_syntax(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.code.parse_string(node.value)


@constructor('!email')
def construct_email(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.email.parse_string(node.value)


@constructor('!url')
def construct_url(
        loader: CustomLoader,
        node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.url.parse_string(node.value)


@constructor('!video_url')
def construct_video_url(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.video_url.parse_string(node.value)


@constructor('!stdnum')
def construct_stdnum(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.stdnum.parse_string(node.value)


@constructor('!chip_nr')
def construct_chip_nr(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.chip_nr.parse_string(node.value)


@constructor('!date')
def construct_date(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.date.parse_string(node.value)


@constructor('!datetime')
def construct_datetime(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.datetime.parse_string(node.value)


@constructor('!time')
def construct_time(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.time.parse_string(node.value)


@constructor('!radio')
def construct_radio(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.radio.parse_string(node.value)


@constructor('!checkbox')
def construct_checkbox(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.checkbox.parse_string(node.value)


@constructor('!fileinput')
def construct_fileinput(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.fileinput.parse_string(node.value)


@constructor('!multiplefileinput')
def construct_multiplefileinput(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.multiplefileinput.parse_string(node.value)


@constructor('!password')
def construct_password(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.password.parse_string(node.value)


@constructor('!decimal_range')
def construct_decimal_range(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.decimal_range.parse_string(node.value)


@constructor('!integer_range')
def construct_integer_range(
    loader: CustomLoader,
    node: ScalarNode
) -> pp.ParseResults:
    return ELEMENTS.integer_range.parse_string(node.value)


def flatten_fieldsets(
    fieldsets: Iterable[Fieldset]
) -> Iterator[ParsedField]:
    for fieldset in fieldsets:
        yield from flatten_fields(fieldset.fields)


def flatten_fields(
    fields: Sequence[ParsedField] | None
) -> Iterator[ParsedField]:

    for field in fields or []:
        yield field

        if hasattr(field, 'fields'):
            yield from flatten_fields(field.fields)

        if hasattr(field, 'choices'):
            for choice in field.choices:
                yield from flatten_fields(choice.fields)


def find_field(
    fieldsets: Iterable[Fieldset],
    id: str | None
) -> Fieldset | ParsedField | None:

    id = as_internal_id(id or '')

    for fieldset in fieldsets:
        if fieldset.id == id:
            return fieldset

        if not fieldset.id or id.startswith(fieldset.id):
            for field in flatten_fields(fieldset.fields):
                if field.id == id:
                    return field
    return None


class Fieldset:
    """ Represents a parsed fieldset. """

    def __init__(
        self,
        label: str,
        fields: Sequence[ParsedField] | None = None
    ):
        self.label = label if label != '...' else None
        self.fields = fields or []

    @property
    def id(self) -> str:
        return as_internal_id(self.human_id)

    @property
    def human_id(self) -> str:
        return self.label or ''

    def find_field(
        self,
        id: str | None = None
    ) -> Fieldset | ParsedField | None:
        return find_field((self,), id=id)


class Choice:
    """ Represents a parsed choice.

    Note: Choices may have child-fields which are meant to be shown to the
    user if the given choice was selected.

    """
    def __init__(
        self,
        key: str,
        label: str,
        selected: bool = False,
        fields: Sequence[ParsedField] | None = None
    ):
        self.key = key
        self.label = label
        self.selected = selected
        self.fields = fields


class Field:
    """ Represents a parsed field. """

    def __init__(
        self,
        label: str,
        required: bool,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None,
        human_id: str | None = None,
        **extra_attributes: Any
    ):

        self.label = label
        self._human_id = human_id or label
        self.required = required
        self.parent = parent
        self.fieldset = fieldset
        self.field_help = field_help

        for key, value in extra_attributes.items():
            setattr(self, key, value)

    @property
    def id(self) -> str:
        return as_internal_id(self.human_id)

    @cached_property
    def human_id(self) -> str:
        if self.parent:
            return f'{self.parent.human_id}/{self._human_id}'

        if self.fieldset and self.fieldset.human_id:
            return f'{self.fieldset.human_id}/{self._human_id}'

        return self._human_id

    @classmethod
    def create(  # type:ignore[misc]
        cls: type[_FieldT],
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> _FieldT:

        return cls(  # type:ignore[return-value]
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            field_help=field_help
        )

    # FIXME: This is used in onegov.directory.archive and is honestly
    #        pretty piggy, for now we just let anything pass and
    #        trust that we only emit ValueError, which get turned
    #        into a None on the receiving end, but we should make
    #        this a bit more robust...
    def parse(self, value: Any) -> object:
        return value


@final
class PasswordField(Field):
    type: ClassVar[Literal['password']] = 'password'


@final
class EmailField(Field):
    type: ClassVar[Literal['email']] = 'email'


@final
class UrlField(Field):
    type: ClassVar[Literal['url']] = 'url'


@final
class VideoURLField(Field):
    type: ClassVar[Literal['video_url']] = 'video_url'


@final
class DateField(Field):
    type: ClassVar[Literal['date']] = 'date'
    valid_date_range: pp.ParseResults

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> DateField:

        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            field_help=field_help,
            valid_date_range=field.valid_date_range
        )

    def parse(self, value: Any) -> object:
        # the first int in an ambiguous date is assumed to be a day
        # (since our software runs in europe first and foremost)
        return dateutil_parser.parse(value, dayfirst=True).date()


@final
class DatetimeField(Field):
    type: ClassVar[Literal['datetime']] = 'datetime'
    valid_date_range: pp.ParseResults

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> DatetimeField:

        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            field_help=field_help,
            valid_date_range=field.valid_date_range
        )

    def parse(self, value: Any) -> object:
        # the first int in an ambiguous date is assumed to be a day
        # (since our software runs in europe first and foremost)
        return dateutil_parser.parse(value, dayfirst=True)


@final
class TimeField(Field):
    type: ClassVar[Literal['time']] = 'time'

    def parse(self, value: Any) -> object:
        return time(*map(int, value.split(':')))


@final
class StringField(Field):
    type: ClassVar[Literal['text']] = 'text'
    maxlength: int | None
    regex: Pattern[str] | None

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> StringField:
        regex = field.regex and re.compile(field.regex) or None

        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            maxlength=field.length or None,
            regex=regex,
            field_help=field_help
        )


@final
class TextAreaField(Field):
    type: ClassVar[Literal['textarea']] = 'textarea'
    rows: int | None

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> TextAreaField:
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            rows=field.rows or None,
            field_help=field_help
        )


@final
class CodeField(Field):
    type: ClassVar[Literal['code']] = 'code'
    syntax: str

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> CodeField:
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            syntax=field.syntax,
            field_help=field_help
        )


@final
class StdnumField(Field):
    type: ClassVar[Literal['stdnum']] = 'stdnum'
    format: str

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> Self:
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            format=field.format,
            field_help=field_help
        )


@final
class ChipNrField(Field):
    type: ClassVar[Literal['chip_nr']] = 'chip_nr'


@final
class IntegerRangeField(Field):
    type: ClassVar[Literal['integer_range']] = 'integer_range'
    pricing: PricingRules
    range: range

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> IntegerRangeField:

        if field.pricing:
            label = identifier.label + format_pricing(field.pricing)
            # map one price to the whole range, the price will be
            # multiplied by the selected value from the range
            pricing = {field[0]: field.pricing}
        else:
            label = identifier.label
            pricing = None

        return cls(
            # only modify the label visually, we don't want to
            # affect the field id
            human_id=identifier.label,
            label=label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            range=field[0],
            pricing=pricing,
            field_help=field_help
        )

    def parse(self, value: Any) -> object:
        return int(float(value))  # automatically truncates dots


@final
class DecimalRangeField(Field):
    type: ClassVar[Literal['decimal_range']] = 'decimal_range'
    range: decimal_range

    @classmethod
    def create(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> DecimalRangeField:
        return cls(
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            range=field[0],
            field_help=field_help

        )

    def parse(self, value: Any) -> object:
        return Decimal(value)


class FileinputBase:
    extensions: list[str]

    @classmethod
    def create(  # type:ignore[misc]
        cls: type[_FieldT],
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> _FieldT:
        return cls(  # type:ignore[return-value]
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            extensions=field.extensions,
            field_help=field_help
        )


@final
class FileinputField(FileinputBase, Field):
    type: ClassVar[Literal['fileinput']] = 'fileinput'


@final
class MultipleFileinputField(FileinputBase, Field):
    type: ClassVar[Literal['multiplefileinput']] = 'multiplefileinput'


class OptionsField:
    choices: list[Choice]
    pricing: PricingRules
    discount: dict[str, float]

    @classmethod
    def create(  # type:ignore[misc]
        cls: type[_FieldT],
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        parent: ParsedField | None = None,
        fieldset: Fieldset | None = None,
        field_help: str | None = None
    ) -> _FieldT:

        choices = [
            Choice(
                key=c.label,
                label=(
                    c.label
                    + format_pricing(c.pricing)
                    + format_discount(c.discount)
                ),
                selected=c.checked
            )
            for c in field.choices
        ]

        pricing = {c.label: c.pricing for c in field.choices if c.pricing}
        discount = {
            c.label: c.discount.amount / Decimal('100')
            for c in field.choices
            if c.discount
        }

        return cls(  # type:ignore[return-value]
            label=identifier.label,
            required=identifier.required,
            parent=parent,
            fieldset=fieldset,
            choices=choices,
            pricing=pricing or None,
            discount=discount or None,
            field_help=field_help
        )

    def parse(self, value: Any) -> Any:
        if isinstance(value, str):
            return [v.strip() for v in value.split('\n')]

        return value


@final
class RadioField(OptionsField, Field):
    type: ClassVar[Literal['radio']] = 'radio'

    def parse(self, value: Any) -> object:
        v = super().parse(value)
        return v and v[0] or None


@final
class CheckboxField(OptionsField, Field):
    type: ClassVar[Literal['checkbox']] = 'checkbox'


@lru_cache(maxsize=1)
def parse_formcode(
    formcode: str,
    enable_edit_checks: bool = False
) -> list[Fieldset]:
    """ Takes the given formcode and returns an intermediate representation
    that can be used to generate forms or do other things.

    :param formcode: string representing formcode to be parsed
    :param enable_edit_checks: bool to activate additional check after
    editing the form. Should only be active originating from
    forms.validators.py
    """
    # CustomLoader is inherited from SafeLoader so no security issue here
    parsed = yaml.load(  # nosec B506
        '\n'.join(translate_to_yaml(formcode, enable_edit_checks)),
        CustomLoader
    )

    fieldsets = []
    field_classes: dict[str, type[ParsedField]] = {
        cls.type: cls  # type:ignore
        for cls in Field.__subclasses__()
    }
    used_ids: set[str] = set()

    for fieldset in parsed:

        # fieldsets occur only at the top level
        label = next(k for k in fieldset.keys())
        fs = Fieldset(label)

        fs.fields = [
            parse_field_block(block, field_classes, used_ids, fs)
            for block in (fieldset[label] or ())
        ]
        if enable_edit_checks and not fs.fields:
            raise errors.EmptyFieldsetError(label)

        fieldsets.append(fs)

    return fieldsets


def parse_field_block(
    # FIXME: This is very loose, we could do better, but we want to
    #        refactor form parsing anyways...
    field_block: dict[str, Any],
    field_classes: dict[str, type[ParsedField]],
    used_ids: set[str],
    fieldset: Fieldset,
    parent: ParsedField | None = None
) -> ParsedField:
    """ Takes the given parsed field block and yields the fields from it """

    key, field = next(i for i in field_block.items())
    field_help = field_block.get('field_help')

    identifier_src = key.rstrip('= ') + '='
    identifier = ELEMENTS.identifier.parseString(identifier_src)

    # add the nested options/dependencies in case of radio/checkbox buttons
    if isinstance(field, list):
        choices = [next(i for i in f.items()) for f in field]

        for choice, dependencies in choices:
            choice['dependencies'] = dependencies

        choices = [c[0] for c in choices]

        field = Bunch(choices=choices, type=choices[0].type)

        # make sure only one type is found (either radio or checkbox)
        types = {f.type for f in field.choices}
        assert types <= {'radio', 'checkbox'}

        if not len(types) == 1:
            raise errors.MixedTypeError(key)

    result: ParsedField = field_classes[field.type].create(
        field, identifier, parent, fieldset, field_help)

    if result.id in used_ids:
        raise errors.DuplicateLabelError(label=result.label)

    used_ids.add(result.id)

    # go through nested blocks and recursively add them
    if result.type == 'radio' or result.type == 'checkbox':
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


def format_pricing(pricing: ParseResults | None) -> str:
    if not pricing:
        return ''

    return ' ({:.2f} {})'.format(pricing.amount, pricing.currency)


def format_discount(discount: ParseResults | None) -> str:
    if not discount:
        return ''

    return ' ({:.2f}%)'.format(discount.amount)


def match(expr: pp.ParserElement, text: str) -> bool:
    """ Returns true if the given parser expression matches the given text. """
    try:
        expr.parseString(text)
    except pp.ParseBaseException:
        return False
    else:
        return True


def try_parse(expr: pp.ParserElement, text: str) -> pp.ParseResults | None:
    """ Returns the result of the given parser expression and text, or None.

    """
    try:
        return expr.parseString(text)
    except pp.ParseBaseException:
        return None


def prepare(text: str) -> Iterator[tuple[int, str]]:
    """ Takes the raw form source and prepares it for the translation into
    yaml.

    """

    lines = (l.rstrip() for l in text.split('\n'))
    yield from ensure_a_fieldset((ix, l) for ix, l in enumerate(lines) if l)


def ensure_a_fieldset(
    lines: Iterable[tuple[int, str]]
) -> Iterator[tuple[int, str]]:
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


def validate_indent(indent: str) -> bool:
    """
    Returns `False` if indent is other than a multiple of 4, else True
    """
    if len(indent) % 4 != 0:
        return False
    return True


def translate_to_yaml(
    text: str,
    enable_edit_checks: bool = False
) -> Iterator[str]:
    """ Takes the given form text and constructs an easier to parse yaml
    string.

    :param text: string to be parsed
    :param enable_edit_checks: bool to activate additional checks after
    editing a form. Should only be active originating from forms.validators.py
    """

    lines = ((ix, l) for ix, l in prepare(text))
    expect_nested = False
    actual_fields = 0
    ix = 0

    def escape_single(text: str) -> str:
        return text.replace("'", "''")

    def escape_double(text: str) -> str:
        return text.replace('"', '\\"')

    for ix, line in lines:

        indent = ' ' * (4 + (len(line) - len(line.lstrip())))
        if enable_edit_checks and not validate_indent(indent):
            raise errors.InvalidIndentSyntax(line=ix + 1)

        # the top level are the fieldsets
        if match(ELEMENTS.fieldset_title, line):
            yield '- "{}":'.format(escape_double(line.lstrip('# ').rstrip()))
            expect_nested = False
            continue

        # fields are nested lists of dictionaries
        try:
            parse_result = try_parse(ELEMENTS.single_line_fields, line)
        except re.error as exception:
            raise errors.InvalidFormSyntax(line=ix + 1) from exception

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

        # help descriptions following a field
        parse_result = try_parse(ELEMENTS.help_identifier, line)
        if parse_result is not None:
            yield '{indent}"{identifier}": \'{message}\''.format(
                indent=indent + 2 * ' ',
                identifier='field_help',
                message=parse_result.message
            )
            continue

        # checkboxes/radios come without identifier
        parse_result = try_parse(ELEMENTS.boxes, line)
        if parse_result is not None:

            if not expect_nested:
                raise errors.InvalidFormSyntax(line=ix + 1)

            yield "{indent}- !{type} '{definition}':".format(
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
