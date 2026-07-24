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

from datetime import date as date_t  # noqa: TC003
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from functools import lru_cache
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import CoreSchema, core_schema
from pydantic_extra_types.currency_code import Currency  # noqa: TC002

from onegov.core.utils import Bunch
from onegov.form import errors
from onegov.form.parser.grammar import approximate_total_days
from onegov.form.parser.grammar import checkbox
from onegov.form.parser.grammar import chip_nr
from onegov.form.parser.grammar import code
from onegov.form.parser.grammar import date
from onegov.form.parser.grammar import datetime
from onegov.form.parser.grammar import decimal_range_field
from onegov.form.parser.grammar import email
from onegov.form.parser.grammar import field_help_identifier
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


from typing import final, overload, Annotated, Any, Literal, Self
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from builtins import type as type_t
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue
    from pyparsing import ParseResults
    from re import Pattern
    from yaml.nodes import ScalarNode


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


class constructor:  # ruff:ignore[invalid-class-name]
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


@overload
def flatten_fields(
    fields: Sequence[ParsedField] | None,
    with_human_id: Literal[False] = False,
    parent_id: str | None = None
) -> Iterator[ParsedField]: ...
@overload
def flatten_fields(
    fields: Sequence[ParsedField] | None,
    with_human_id: Literal[True],
    parent_id: str | None = None
) -> Iterator[tuple[str, ParsedField]]: ...
@overload
def flatten_fields(
    fields: Sequence[ParsedField] | None,
    with_human_id: bool,
    parent_id: str | None = None
) -> Iterator[ParsedField] | Iterator[tuple[str, ParsedField]]: ...


def flatten_fields(
    fields: Sequence[ParsedField] | None,
    # NOTE: You only know what id a field has, if you know its parent
    #       which gets lost when flattening, so this gives you that
    #       information back.
    with_human_id: bool = False,
    parent_id: str | None = None
) -> Iterator[ParsedField] | Iterator[tuple[str, ParsedField]]:

    for field in fields or ():
        if with_human_id:
            human_id = field.human_id(parent_id)
            yield human_id, field
        else:
            human_id = None
            yield field

        if hasattr(field, 'choices'):
            for choice in field.choices:
                yield from flatten_fields(
                    choice.fields,
                    with_human_id,
                    human_id
                )


def find_field(
    fields: Iterable[ParsedField],
    id: str | None,
    parent_id: str | None = None
) -> ParsedField | None:

    id = as_internal_id(id or '')
    if parent_id and not id.startswith(parent_id):
        return None

    for field in fields:
        field_id = field.id(parent_id)
        if field_id == id:
            return field

        if id.startswith(field_id) and hasattr(field, 'choices'):
            for choice in field.choices:
                result = find_field(choice.fields, id, field_id)
                if result is not None:
                    return result
    return None


def serialize_relativedelta(value: relativedelta) -> dict[str, int]:
    return {
        key: val
        # NOTE: weeks get folded into days
        for key in ('years', 'months', 'days')
        if (val := getattr(value, key, 0))
    }


class _RelativeDeltaAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.literal_schema([
                        'years',
                        'months',
                        'weeks',
                        'days'
                    ]),
                    values_schema=core_schema.int_schema(),
                ),
                core_schema.no_info_plain_validator_function(
                    lambda data: relativedelta(**data)
                ),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(relativedelta),
                from_dict_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize_relativedelta,
                info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            'type': 'object',
            'properties': {
                'years': {'type': 'integer'},
                'months': {'type': 'integer'},
                'weeks': {'type': 'integer'},
                'days': {'type': 'integer'},
            },
            'additionalProperties': False,
        }


RelativeDelta = Annotated[relativedelta, _RelativeDeltaAnnotation]


class _RangeValidationMixin:
    if TYPE_CHECKING:
        start: Any | None
        end: Any | None

    @model_validator(mode='after')
    def start_before_end(self) -> Self:
        start, end = self.start, self.end
        if start is None or end is None:
            return self

        if isinstance(start, relativedelta):
            start = approximate_total_days(start)
            end = approximate_total_days(end)

        if start < end:
            return self

        raise ValueError('Invalid range. Starts needs to be smaller than end.')


class Range[T](BaseModel, _RangeValidationMixin):
    """
    A bounded range, between start and end
    """

    model_config = ConfigDict(frozen=True)

    start: T = Field(
        description='The start of the range.'
    )
    stop: T = Field(
        description='The end of the range. Needs to be larger than the start.'
    )


class RangeEndOptional[T](BaseModel, _RangeValidationMixin):
    """
    A half-bounded range, between start and optional end
    """
    model_config = ConfigDict(frozen=True)

    start: T = Field(
        description='The start of the range.'
    )
    stop: T | None = Field(
        default=None,
        description='The end of the range. Needs to be larger than the start.'
    )


class RangeStartOptional[T](BaseModel, _RangeValidationMixin):
    """
    A half-bounded range, between optional start and end
    """
    model_config = ConfigDict(frozen=True)

    start: T | None = Field(
        default=None,
        description='The start of the range.'
    )
    stop: T = Field(
        description='The end of the range. Needs to be larger than the start. '
            'as long as start is specified.'
    )


type HalfBoundedRange[T] = RangeEndOptional[T] | RangeStartOptional[T]
type DateRange = Range[date_t] | HalfBoundedRange[RelativeDelta]


class Pricing(BaseModel):
    """
    Pricing information for a priced form input or selection.
    """
    model_config = ConfigDict(frozen=True)

    amount: Decimal = Field(
        description='The total decimal cost amount of the selection. '
            'For numeric inputs, this is the price per item. So it will '
            'be multiplied by the quantity input by the user.',
        decimal_places=2
    )
    currency: Currency = Field(
        default=Currency('CHF'),
        description='An ISO 4217 currency code, excluding bonds testing '
            'codes and precious metals. Generally this is expected to be '
            '``CHF`` within this application.'
    )
    online_payment_required: bool = Field(
        default=False,
        description='Whether or not this selection forces the payment to be '
            'made online, directly after form submission. This is useful '
            'for forms, where e.g. the deliverable can optionally be '
            'delivered via the postal service, so when the delivery option '
            'is selected, paying in person is no longer a possibility.'
    )

    def as_tuple(self) -> tuple[Decimal, str, bool]:
        return self.amount, self.currency, self.online_payment_required

    def __str__(self) -> str:
        suffix = '!' if self.online_payment_required else ''
        return f'{self.amount} {self.currency}{suffix}'


# tagged unions so we can type narrow by type field
type BasicParsedField = Annotated[
    PasswordField | EmailField | UrlField | VideoURLField | DateField
    | DatetimeField | TimeField | StringField | TextAreaField
    | CodeField | StdnumField | IntegerRangeField | DecimalRangeField
    | RadioField | CheckboxField | ChipNrField,
    Field(discriminator='kind')
]
type FileParsedField = Annotated[
    FileinputField | MultipleFileinputField,
    Field(discriminator='kind')
]
type ParsedField = Annotated[
    BasicParsedField | FileParsedField,
    Field(discriminator='kind')
]


class Choice(BaseModel):
    """ Represents a single choice of a ``radio`` or ``checkbox`` field.

    Generally the choices are rendered as HTML ``<input type="radio">``
    and  ``<input type="checkbox">`` respecitvely, based on the ``kind``
    of the containing field.

    Choices may contain subfields, which are only displayed as long
    as this choice has been selected.

    """

    model_config = ConfigDict(frozen=True)

    label: str = Field(
        description='The label of this option. The label must be unique '
            'within the containing radio or checkbox field, since it doubles '
            'as the value, that will be stored for this selection.'
    )
    selected: bool = Field(
        default=False,
        description='Whether or not this choice should be pre-selected. '
            'For radio fields only a single choice may be pre-selected.'
    )
    fields: tuple[ParsedField, ...] = Field(
        default=(),
        description='Any subfields that should only be displayed as long '
            'as this choice has been selected. Subfields will inherit the '
            'fieldset of the parent field, unless it explicitly is set '
            'to a non-empty string.'
    )
    pricing: Pricing | None = Field(
        description='The pricing applied when this choice is selected. '
            'This field is mutually exclusive with ``discount``.'
    )
    discount: Decimal | None = Field(
        description='The discount applied when this choice is selected '
            'specified as a percentage. I.e. 50% means the total price '
            'of the form submission is cut in half. Negative percentages '
            'are allowed as procentual surcharge. I.e. -5% means an '
            'additional fee equivalent to 5% of the total price is charged. '
            'This field is mutually exclusive with ``pricing``. If the '
            'applied discounts would result in a negative price, it will '
            'truncate to zero and be treated as a free submission.'
    )

    @model_validator(mode='after')
    def pricing_and_discount_are_mutually_exclusive(self) -> Self:
        if self.pricing is not None and self.discount is not None:
            raise ValueError(
                'You may only specify "pricing" or "discount", not both.'
            )
        return self

    @property
    def display_label(self) -> str:
        if self.pricing is not None:
            return f'{self.label} ({self.pricing}%)'
        if self.discount is not None:
            return f'{self.label} ({self.discount:.2f}%)'
        return self.label


def human_id(label: str, fieldset: str, parent_id: str | None = None) -> str:
    if parent_id:
        return f'{parent_id}/{label}'

    if fieldset:
        return f'{fieldset}/{label}'

    return label


class BaseField[KindT: str](BaseModel):
    """ Represents a form field. """

    model_config = ConfigDict(frozen=True)

    type: KindT = Field(
        description='The type of form field this is. This corresponds to the '
            'HTML input type in some cases. But also includes some additional '
            'custom fields.'
    )
    label: str = Field(
        description='A human readable label for the field. Must be unique '
            'within the same fieldset and/or choice, when it is a subfield. '
            'Since the field identifier is generated from the parent '
            'identifier and fieldset and normalized, it is possible for '
            'two distinct labels to conflict, if they result in the same '
            'identifier after normalization.'
    )
    required: bool = Field(
        default=False,
        description='Whether or not this field is required. Fields that '
            'are not required, can be left empty, when submitting the form.'
    )
    fieldset: str = Field(
        default='',
        description='Fields are grouped into fieldsets based on this '
            'human readable label. Fields in the same fieldset should '
            'appear together sequentially, they will not be reordered, '
            'in order to fit them into the same fieldset. If the same '
            'label occurs twice, but is interrupted by a different label, '
            'it will result in two distinct fieldsets, similar to how '
            '`itertools.groupby` works.'
    )
    field_help: str | None = Field(
        default=None,
        description='For short help texts this might be rendered '
            'inline as a `placeholder` attribute on the HTML input. '
            'Longer text, or text containing newlines will be rendered '
            'as Markdown and rendered between the field label and the '
            'field input.'
    )

    def id(self, parent_id: str | None = None) -> str:
        return as_internal_id(
            human_id(self.label, self.fieldset, parent_id)
        )

    def human_id(self, parent_id: str | None = None) -> str:
        return human_id(self.label, self.fieldset, parent_id)

    @property
    def display_label(self) -> str:
        return self.label

    # FIXME: This is used in onegov.directory.archive and is honestly
    #        pretty piggy, for now we just let anything pass and
    #        trust that we only emit ValueError, which get turned
    #        into a None on the receiving end, but we should make
    #        this a bit more robust...
    def parse(self, value: Any) -> object:
        return value

    @classmethod
    def from_parse_results[T: ParsedField](  # type:ignore[misc]
        cls: type_t[T],
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> T:
        return cls.model_validate({  # type:ignore[return-value]
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help
        })


@final
class PasswordField(BaseField[Literal['password']]):
    """
    Represents an HTML ``<input type="password">``.
    """

    type: Literal['password'] = 'password'


@final
class EmailField(BaseField[Literal['email']]):
    """
    Represents an HTML ``<input type="email">``.
    """

    type: Literal['email'] = 'email'


@final
class UrlField(BaseField[Literal['url']]):
    """
    Represents an HTML ``<input type="url">``.
    """

    type: Literal['url'] = 'url'


@final
class VideoURLField(BaseField[Literal['video_url']]):
    """
    Represents an HTML ``<input type="url">`` pointing to a video.
    """

    type: Literal['video_url'] = 'video_url'


@final
class DateField(BaseField[Literal['date']]):
    """
    Represents an HTML ``<input type="date">``.
    """

    type: Literal['date'] = 'date'
    valid_date_range: DateRange | None = None

    def parse(self, value: Any) -> object:
        # the first int in an ambiguous date is assumed to be a day
        # (since our software runs in europe first and foremost)
        return dateutil_parser.parse(value, dayfirst=True).date()

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'valid_date_range': field.valid_date_range,
        })


@final
class DatetimeField(BaseField[Literal['datetime']]):
    """
    Represents an HTML ``<input type="datetime-local">``.
    """

    type: Literal['datetime'] = 'datetime'
    valid_date_range: DateRange | None = None

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'valid_date_range': field.valid_date_range,
        })


@final
class TimeField(BaseField[Literal['time']]):
    """
    Represents an HTML ``<input type="time">``.
    """

    type: Literal['time'] = 'time'

    def parse(self, value: Any) -> object:
        return time(*map(int, value.split(':')))


@final
class StringField(BaseField[Literal['text']]):
    """
    Represents an HTML ``<input type="text">``.
    """
    type: Literal['text'] = 'text'
    maxlength: int | None = Field(
        default=None,
        description='Sets the `maxlength` attribute on the HTML text input'
    )
    regex: Pattern[str] | None = Field(
        default=None,
        description='Validates the user-submitted text input against this '
            'regex pattern. Generally these patterns should include beginning '
            'and end markers, e.g. `^[0-9]{0,4}$` for a 4-digit numeric code.'
    )

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'regex': field.regex,
            'maxlength': field.length or None,
        })


@final
class TextAreaField(BaseField[Literal['textarea']]):
    """
    Represents an HTML ``<textarea>``.
    """
    type: Literal['textarea'] = 'textarea'
    rows: int | None = Field(
        default=None,
        gt=0,
        description='Sets the `rows` attribute on the HTML textarea'
    )

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'rows': field.rows or None,
        })


@final
class CodeField(BaseField[Literal['code']]):
    """
    Represents an HTML ``<textarea>`` accepting code with a specified syntax.

    Currently only markdown syntax is supported.
    """
    type: Literal['code'] = 'code'
    syntax: Literal['markdown'] = 'markdown'

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'syntax': field.syntax,
        })


@final
class StdnumField(BaseField[Literal['stdnum']]):
    """
    Represents an HTML ``<input type="text">`` accepting a specified standard
    number or code format. E.g. IBAN numbers.
    """
    type: Literal['stdnum'] = 'stdnum'
    # FIXME: Ideally we would list all of the valid stdnum modules here
    #        so we get a proper constraint in the JSON schema, but that
    #        means loading and walking all the stdnum modules recursively
    #        which would slow down startup times. So for now we don't
    #        validate this
    format: str = Field(
        pattern=r'[a-z\.]+',
        description='A valid module name in the stdnum namespace of the '
            'python-stdnum package. E.g. for validating IBAN numbers you '
            'would supply "iban", since the module lives at `stdnum.iban`. '
            'For validating swiss social security numbers you would supply '
            '"ch.ssn".'
    )

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'format': field.format,
        })


@final
class ChipNrField(BaseField[Literal['chip_nr']]):
    """
    Represents an HTML ``<input type="text">`` accepting 15-digit animal
    identification numbers.
    """
    type: Literal['chip_nr'] = 'chip_nr'


@final
class IntegerRangeField(BaseField[Literal['integer_range']]):
    """
    Represents an HTML ``<input type="number">`` accepting integer values
    within the specified range.
    """

    type: Literal['integer_range'] = 'integer_range'
    range: Range[int]
    pricing_per_item: Pricing | None = Field(
        default=None,
        description='The pricing is multiplied by the quantity submitted '
            'by this numeric input'
    )

    @property
    def display_label(self) -> str:
        if self.pricing_per_item is None:
            return self.label

        return f'{self.label} ({self.pricing_per_item})'

    def parse(self, value: Any) -> object:
        return int(float(value))  # automatically truncates dots

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        pricing = field.pricing
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'range': {
                'start': field[0].start,
                'stop': field[0].stop,
            },
            'pricing': {
                'amount': pricing.amount,
                'currency': pricing.currency,
                'online_payment_required': pricing.credit_card_payment
            } if pricing else None,
        })


@final
class DecimalRangeField(BaseField[Literal['decimal_range']]):
    """
    Represents an HTML ``<input type="number">`` accepting values
    within the specified range.
    """
    type: Literal['decimal_range'] = 'decimal_range'
    range: Range[Decimal]

    def parse(self, value: Any) -> object:
        return Decimal(value)

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'range': {
                'start': field[0].start,
                'stop': field[0].stop,
            },
        })


@final
class FileinputField(BaseField[Literal['fileinput']]):
    """
    Represents an HTML ``<input type="file">`` accepting a single
    file matching the specified file extensions.
    """
    type: Literal['fileinput'] = 'fileinput'
    extensions: tuple[str, ...] = Field(
        description='If arbitrary file uploads are allowed, then this '
            'should contain a single element with the value ``*``. If '
            'more than one element is specified, all of them are treated '
            'like real file extensions. Generally this only works for '
            'file extensions with a well known set of associated mimetypes.',
        min_length=1,
    )

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'extensions': field.extensions,
        })


@final
class MultipleFileinputField(BaseField[Literal['multiplefileinput']]):
    """
    Represents an HTML ``<input type="file" multiple>`` accepting multiple
    files matching the specified file extensions.
    """
    type: Literal['multiplefileinput'] = 'multiplefileinput'
    extensions: tuple[str, ...] = Field(
        description='If arbitrary file uploads are allowed, then this '
            'should contain a single element with the value ``*``. If '
            'more than one element is specified, all of them are treated '
            'like real file extensions. Generally this only works for '
            'file extensions with a well known set of associated mimetypes.',
        min_length=1,
    )

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            'extensions': field.extensions,
        })


@final
class RadioField(BaseField[Literal['radio']]):
    type: Literal['radio'] = 'radio'
    choices: tuple[Choice, ...] = Field(
        description='A sequence of choices. One of them may be pre-selected. '
            'Each choice will be rendered as a HTML ``<input type="radio">``.',
        # NOTE: This probably should be 2 for radio fields, but we have
        #       never restricted this, so there's no reason to start
        #       doing it now, especially, since it is harmless.
        min_length=1
    )

    def parse(self, value: Any) -> object:
        if isinstance(value, str):
            return next(iter(v.strip() for v in value.split('\n')), None)
        return value and value[0] or None

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            # NOTE: The heavy lifting of constructing the choices and the
            #       corresponding subfields happen inside parse_field_block.
            'choices': field.choices,
        })


@final
class CheckboxField(BaseField[Literal['checkbox']]):
    type: Literal['checkbox'] = 'checkbox'
    choices: tuple[Choice, ...] = Field(
        description='A sequence of choices. Any number of them may be '
            'pre-selected. Each choice will be rendered  as a HTML '
            '``<input type="checkbox">``.',
        min_length=1
    )

    def parse(self, value: Any) -> Any:
        if isinstance(value, str):
            return [v.strip() for v in value.split('\n')]

        return value

    @classmethod
    def from_parse_results(
        cls,
        field: pp.ParseResults,
        identifier: pp.ParseResults,
        fieldset: str = '',
        field_help: str | None = None
    ) -> Self:
        return cls.model_validate({
            'label': identifier.label,
            'required': identifier.required,
            'fieldset': fieldset,
            'field_help': field_help,
            # NOTE: The heavy lifting of constructing the choices and the
            #       corresponding subfields happen inside parse_field_block.
            'choices': field.choices,
        })


class ParsedForm(BaseModel):
    """
    Represents a parsed form.
    """

    model_config = ConfigDict(frozen=True)

    fields: tuple[ParsedField, ...] = Field(
        discriminator='kind'
    )


@lru_cache(maxsize=1)
def parse_formcode(
    formcode: str,
    enable_edit_checks: bool = False
) -> list[ParsedField]:
    """ Takes the given formcode and returns an intermediate representation
    that can be used to generate forms or do other things.

    :param formcode: string representing formcode to be parsed
    :param enable_edit_checks: bool to activate additional check after
    editing the form. Should only be active originating from
    forms.validators.py
    """
    # CustomLoader is inherited from SafeLoader so no security issue here
    parsed = yaml.load(  # nosec: B506
        '\n'.join(translate_to_yaml(formcode, enable_edit_checks)),
        CustomLoader
    )

    fields = []
    field_classes: dict[str, type[ParsedField]] = {
        cls.type: cls  # type:ignore
        for cls in BaseField.__subclasses__()
    }
    used_ids: set[str] = set()

    for fieldset in parsed:

        # fieldsets occur only at the top level
        label = next(k for k in fieldset.keys())

        fieldset_fields = [
            parse_field_block(block, field_classes, used_ids, label)
            for block in (fieldset[label] or ())
        ]
        if enable_edit_checks and not fieldset_fields:
            raise errors.EmptyFieldsetError(label)

        fields.extend(fieldset_fields)

    return fields


def parse_field_block(
    # FIXME: This is very loose, we could do better, but we want to
    #        refactor form parsing anyways...
    field_block: dict[str, Any],
    field_classes: dict[str, type[ParsedField]],
    used_ids: set[str],
    fieldset: str,
    parent_id: str | None = None
) -> ParsedField:
    """ Takes the given parsed field block and yields the fields from it """

    key, field = next(i for i in field_block.items())
    field_help = field_block.get('field_help')

    if field is None:
        raise errors.FieldCompileError(field_name=key.rstrip('= '))

    identifier_src = key.rstrip('= ') + '='
    identifier = ELEMENTS.identifier.parse_string(identifier_src)

    result_id = as_internal_id(
        human_id(identifier.label, fieldset, parent_id)
    )
    if result_id in used_ids:
        raise errors.DuplicateLabelError(label=identifier.label)

    used_ids.add(result_id)

    # add the nested options/dependencies in case of radio/checkbox buttons
    if isinstance(field, list):
        choices = [next(i for i in f.items()) for f in field]

        # make sure only one type is found (either radio or checkbox)
        types = {c[0].type for c in choices}
        assert types <= {'radio', 'checkbox'}

        if not len(types) == 1:
            raise errors.MixedTypeError(key.rstrip('= '))

        for choice, children in choices:
            if not children:
                continue

            # recursively parse and add children
            choice['fields'] = [
                parse_field_block(
                    field_block=child,
                    field_classes=field_classes,
                    used_ids=used_ids,
                    fieldset=fieldset,
                    parent_id=result_id
                )
                for child in children
            ]

        choices = [c[0] for c in choices]
        field = Bunch(choices=choices, type=choices[0].type)

    return field_classes[field.type].from_parse_results(
        field, identifier, fieldset, field_help)


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
        expr.parse_string(text)
    except pp.ParseBaseException:
        return False
    else:
        return True


def try_parse(expr: pp.ParserElement, text: str) -> pp.ParseResults | None:
    """ Returns the result of the given parser expression and text, or None.

    """
    try:
        return expr.parse_string(text)
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


class IndentStack(list[int]):
    """ Handles the indentation logic for formcode.

    Identifiers are always followed by options and vice versa, so we can
    handle these in the same stack and apply logic based on the current
    size of the stack.

    """
    __slots__ = ('enable_edit_checks', )

    def __init__(self, *, enable_edit_checks: bool = False) -> None:
        super().__init__()
        self.enable_edit_checks = enable_edit_checks

    def is_identifier(self, indent: int) -> bool:
        try:
            return self.index(indent) % 2 == 0
        except ValueError:
            return False

    def handle_indent(
        self,
        line: int,  # for error messages
        indent: int,
        *,
        is_option: bool = False
    ) -> None:
        if not self.enable_edit_checks:
            return

        if not self:
            # the first indentation cannot be an option
            if is_option:
                raise errors.InvalidIndentSyntax(line=line)
            self.append(indent)
            return

        previous_indent = self[-1]
        if previous_indent < indent:
            # add new level
            expect_option = len(self) % 2 == 1
            if is_option is not expect_option:
                raise errors.InvalidIndentSyntax(line=line)
            self.append(indent)
            return

        if previous_indent > indent:
            while len(self) > 1:
                self.pop()
                previous_indent = self[-1]
                if previous_indent == indent:
                    break
            else:
                # the desired indentation matches no previous
                # indentation
                raise errors.InvalidIndentSyntax(line=line)

        expect_option = len(self) % 2 == 0
        if is_option is not expect_option:
            raise errors.InvalidIndentSyntax(line=line)


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
    indent_stack = IndentStack(enable_edit_checks=enable_edit_checks)
    expect_option = False

    def escape_single(text: str) -> str:
        return text.replace("'", "''")

    def escape_double(text: str) -> str:
        return text.replace('"', '\\"')

    for ix, line in lines:
        len_indent = len(line) - len(line.lstrip())
        indent = ' ' * (4 + len_indent)

        if enable_edit_checks and not validate_indent(indent):
            raise errors.InvalidIndentSyntax(line=ix + 1)

        # the top level are the fieldsets
        if match(ELEMENTS.fieldset_title, line):
            if enable_edit_checks and len_indent > 4:
                raise errors.NestedFieldsetError(line=ix + 1)
            yield '- "{}":'.format(escape_double(line.lstrip('# ').rstrip()))
            expect_nested = False
            indent_stack.clear()
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

            indent_stack.handle_indent(ix + 1, len_indent)
            continue

        # help descriptions following a field
        parse_result = try_parse(ELEMENTS.help_identifier, line)
        if parse_result is not None:
            if enable_edit_checks:
                if expect_option or not indent_stack:
                    raise errors.InvalidCommentLocationSyntax(line=ix + 1)

                if not indent_stack.is_identifier(len_indent):
                    raise errors.InvalidCommentIndentSyntax(line=ix + 1)

            yield '{indent}"{identifier}": \'{message}\''.format(
                indent=indent + 2 * ' ',
                identifier='field_help',
                message=escape_single(parse_result.message)
            )
            indent_stack.handle_indent(ix + 1, len_indent)
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

            indent_stack.handle_indent(ix + 1, len_indent, is_option=True)
            expect_option = False
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

            indent_stack.handle_indent(ix + 1, len_indent)
            expect_option = True
            continue

        raise errors.InvalidFormSyntax(line=ix + 1)

    if not actual_fields:
        raise errors.InvalidFormSyntax(line=ix + 1)
