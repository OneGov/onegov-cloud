from __future__ import annotations

import re

from datetime import date as dateobj
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from functools import lru_cache
from onegov.form.utils import decimal_range
from pyparsing import (
    alphanums,
    Combine,
    Group,
    Literal,
    MatchFirst,
    nums,
    pyparsing_unicode,
    OneOrMore,
    Optional,
    ParseFatalException,
    ParserElement,
    Regex,
    Suppress,
    White,
    Word,
)
from pyparsing.util import _collapse_string_to_ranges

from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pyparsing.results import ParseResults
    from re import Pattern

_T = TypeVar('_T')


# we want newlines to be significant
ParserElement.set_default_whitespace_chars(' \t')

printables = pyparsing_unicode.Latin1.printables
text = Word(printables)
numeric = Word(nums)
word_re = rf'[{_collapse_string_to_ranges(printables)}]+'
no_printable_or_whitespace_re = (
    rf'[^{_collapse_string_to_ranges(printables + " ")}]')


@lru_cache(maxsize=16)
def text_without_re(characters: str) -> str:
    """ Returns a re group for text without the given characters. """
    chars = (c for c in printables if c not in characters)
    return rf'[{_collapse_string_to_ranges(chars)}]+'


def text_without(characters: str) -> Word:
    """ Returns all printable text without the given characters. """
    return Word(printables, exclude_chars=characters)


def matches(character: str) -> Callable[[ParseResults], bool]:
    """ Returns true if the given character matches the token. """
    return lambda tokens: tokens and tokens[0] == character or False


def literal(value: _T) -> Callable[[ParseResults], _T]:
    """" Returns the given value, ignoring the tokens alltogether. """
    return lambda tokens: value


def as_int(tokens: ParseResults) -> int | None:
    """ Converts the token to int if possible. """
    return int(tokens[0]) if tokens else None


def as_joined_string(tokens: ParseResults) -> str:
    """ Joins the given tokens into a single string. """
    return ''.join(tokens[0])


def as_decimal(tokens: ParseResults) -> Decimal | None:
    """ Converts the token to decimal if possible. """
    if tokens and tokens[0] == '-':
        tokens = tokens[1:]
        prefix = '-'
    else:
        prefix = '+'

    return Decimal(prefix + '.'.join(tokens)) if tokens else None


def as_uppercase(tokens: ParseResults) -> str | None:
    """ Converts the token to uppercase if possible. """
    return ''.join(tokens).upper() if tokens else None


def as_integer_range(tokens: ParseResults) -> range | None:
    """ Converts the token to an integer range if possible. """
    return range(int(tokens[0]), int(tokens[1])) if tokens else None


def as_decimal_range(tokens: ParseResults) -> decimal_range | None:
    """ Converts the token to a decimal range if possible. """
    return decimal_range(tokens[0], tokens[1]) if tokens else None


def as_regex(tokens: ParseResults) -> Pattern[str] | None:
    """ Converts the token to a working regex if possible. """
    return re.compile(tokens[0]) if tokens else None


def as_date(instring: str, loc: int, tokens: ParseResults) -> dateobj | None:
    """ Converts the token to a date if possible. """
    if not tokens:
        return None
    try:
        return dateobj(int(tokens[0]), int(tokens[1]), int(tokens[2]))
    except ValueError as exception:
        raise ParseFatalException(instring, loc, 'Invalid date') from exception


def approximate_total_days(delta: relativedelta) -> float:
    """ Computes an approximate day delta from a relativedelta. """
    return delta.years * 365.25 + delta.months * 30.5 + delta.days


def is_valid_date_range(
    instring: str,
    loc: int,
    tokens: ParseResults
) -> ParseResults:
    """ Checks if the date range is valid """
    if tokens:
        after, before = tokens
    else:
        # invalid, will be caught below
        after = before = None

    if after is None:
        if before is not None:
            return tokens
        # invalid
    elif before is None:
        return tokens
    elif type(after) is not type(before):
        # invalid
        pass
    elif isinstance(after, relativedelta):
        if approximate_total_days(after) < approximate_total_days(before):
            return tokens
        # invalid
    elif after < before:
        return tokens

    raise ParseFatalException(instring, loc, 'Invalid date range')


def as_relative_delta(tokens: ParseResults) -> relativedelta | None:
    return relativedelta(**{  # type: ignore[arg-type]
        tokens[1]: int(tokens[0])
    }) if tokens else None


def unwrap(tokens: ParseResults) -> Any | None:
    """ Unwraps grouped tokens. """
    return tokens[0] if tokens else None


def tag(**tags: str) -> Callable[[ParseResults], None]:
    """ Takes the given tags and applies them to the token. """
    def apply_tags(tokens: ParseResults) -> None:
        for key, value in tags.items():
            tokens[key] = value
    return apply_tags


def with_whitespace_inside(expr: ParserElement) -> Combine:
    """ Returns an expression that allows for whitespace inside, but not
    outside the expression.

    """
    return Combine(OneOrMore(expr | White(' ', max=1) + expr))


def enclosed_in(expr: ParserElement, characters: str) -> ParserElement:
    """ Wraps the given expression in the given characters. """
    assert len(characters) == 2
    left, right = characters[0], characters[1]
    return Suppress(left) + expr + Suppress(right)


def number_enclosed_in(characters: str) -> ParserElement:
    """ Wraps numers in the given characters, making sure the result is an int.

    """
    return enclosed_in(numeric, characters).set_parse_action(as_int)


def choices_enclosed_in(
    characters: str,
    choices: Sequence[str]
) -> ParserElement:
    """ Wraps the given choices in the given characters, making sure only
    valid choices are possible.

    """
    expr = Regex(f'({"|".join(re.escape(c) for c in choices)})')
    return enclosed_in(expr, characters).set_parse_action(unwrap)


def mark_enclosed_in(characters: str) -> MatchFirst:
    """ Returns a mark (x) inclosed in the given characters. For example,
    ``mark_enclosed_in('[]')`` creates an expression that accepts any of these
    and sets the result of the 'x' value to True, the others to False::

        [x]
        [ ]
    """
    assert len(characters) == 2
    left, right = characters[0], characters[1]
    return MatchFirst((
        Literal(left + 'x' + right).set_parse_action(literal(True)),
        Literal(left + ' ' + right).set_parse_action(literal(False))
    ))


def textfield() -> ParserElement:
    """ Returns a textfield parser.

    Example::

        ____[50]

    The number defines the maximum length.

    Additionally, a regex may be specified to validate the field::

        ___/[0-9]{4}

    """
    length = number_enclosed_in('[]')('length')

    regex = Word(printables).set_parse_action(as_regex)('regex')
    regex = Suppress('/') + regex

    textfield = Suppress('___') + Optional(length) + Optional(regex)
    textfield.set_parse_action(tag(type='text'))

    return textfield


def textarea() -> ParserElement:
    """ Returns a textarea parser.

    Example::

        ...[5]

    The number defines the number of rows.

    """

    rows = number_enclosed_in('[]')('rows')

    textarea = Suppress('...') + Optional(rows)
    textarea.set_parse_action(tag(type='textarea'))

    return textarea


def code() -> ParserElement:
    """ Returns a code textfield with a specified syntax.

    Currently only markdown is supported.

    Example::

        <markdown>

    """

    code = choices_enclosed_in('<>', ('markdown', ))('syntax')
    code.add_parse_action(tag(type='code'))

    return code


def password() -> ParserElement:
    """ Returns a password field parser.

    Example::

        ***

    """

    return Suppress('***').set_parse_action(tag(type='password'))


def email() -> ParserElement:
    """ Returns an email field parser.

    Example::

        @@@

    """
    return Suppress('@@@').set_parse_action(tag(type='email'))


def url() -> ParserElement:
    """ Returns an url field parser.

    Example::

        http://
        https://

    """
    return Suppress(Regex(r'https?://')).set_parse_action(tag(type='url'))


def video_url() -> ParserElement:
    """ Returns an video url field parser.

    Example::

        video-url

    """
    return Suppress(Regex(r'video-url')).set_parse_action(tag(
        type='video_url'))


def absolute_date() -> ParserElement:
    """ Returns an absolute date parser.

    Example::

        2020.10.10
    """
    date_expr = numeric + Suppress('.') + numeric + Suppress('.') + numeric
    return date_expr.set_parse_action(as_date)


def relative_delta() -> ParserElement:
    """ Returns a relative delta parser.

    Example::

        +1 days
        -4 weeks
        0 years
    """

    sign = Optional(Literal('-') | Literal('+'))
    grain = (Literal('days') | Literal('weeks') | Literal('months')
             | Literal('years'))
    return (
        Combine(sign + numeric) + grain
    ).set_parse_action(as_relative_delta)


def valid_date_range() -> ParserElement:
    """ Returns a valid date range parser.

    Example::

        (..today)
        (2010.01.01..2020.01.01)
        (-2 weeks..+4 months)

    """

    today = Literal('today').set_parse_action(
        literal(relativedelta()))
    value_expr = Optional(
        today | relative_delta() | absolute_date(),
        default=None
    )
    date_range = value_expr('start') + Suppress('..') + value_expr('stop')
    date_range.set_parse_action(is_valid_date_range)
    return Group(enclosed_in(date_range, '()'))('valid_date_range')


def date() -> ParserElement:
    """ Returns a date parser.

    Example::

        YYYY.MM.DD

    """

    date = Suppress('YYYY.MM.DD').set_parse_action(tag(type='date'))
    return date + Optional(valid_date_range())


def datetime() -> ParserElement:
    """ Returns a datetime parser.

    Example::

        YYYY.MM.DD HH:MM

    """

    dt = Suppress('YYYY.MM.DD HH:MM').set_parse_action(tag(type='datetime'))
    return dt + Optional(valid_date_range())


def time() -> ParserElement:
    """ Returns a time parser.

    Example::

        HH:MM

    """

    return Suppress('HH:MM').set_parse_action(tag(type='time'))


def stdnum() -> ParserElement:
    """ Returns an stdnum parser.

    Example::

        # iban

    """
    prefix = Suppress('#') + Optional(White(' '))
    parser = prefix + Regex(r'[a-z\.]+')('format')
    parser.set_parse_action(tag(type='stdnum'))

    return parser


def chip_nr() -> ParserElement:
    """ Returns a chip number parser.

    Example::

        chip-nr

    """
    return Suppress(Regex(r'chip-nr')).set_parse_action(tag(type='chip_nr'))


def fileinput() -> ParserElement:
    """ Returns a fileinput parser.

    For all kindes of files::

        *.*

    For specific files::

        *.pdf|*.doc

    For multiple file upload::

        *.pdf (multiple)

    """
    any_extension = Suppress('*.*')
    some_extension = Suppress('*.') + Word(alphanums) + Optional(Suppress('|'))
    extensions = Group(any_extension | OneOrMore(some_extension))
    multiple = enclosed_in(Literal('multiple'), '()')

    def extract_file_types(tokens: ParseResults) -> None:
        if len(tokens) == 2 and tokens[1] == 'multiple':
            tokens['type'] = 'multiplefileinput'
        else:
            tokens['type'] = 'fileinput'

        if len(tokens[0]) == 0:
            tokens['extensions'] = ['*']
        else:
            tokens['extensions'] = [ext.lower() for ext in tokens[0].asList()]

    parser = extensions + Optional(multiple)
    parser.set_parse_action(extract_file_types)

    return parser


def decimal() -> ParserElement:
    """ Returns a decimal parser.

    Decimal point is '.'.

    For example:

        0.00
        123
        11.1
        -10.0

    """

    return (
        (Optional('-') + numeric + Optional(Suppress('.') + numeric))
        .set_parse_action(as_decimal)('amount')
    )


def range_field(
    value_expression: ParserElement,
    parse_action: Callable[[ParseResults], Any],
    type: str
) -> ParserElement:
    """ Generic range field parser. """

    r = (value_expression + Suppress('..') + value_expression)
    r = r.set_parse_action(parse_action)
    r = r.add_parse_action(tag(type=type))

    return r


def integer_range_field() -> ParserElement:
    """ Returns an integer range parser. """

    number = Combine(Optional('-') + numeric)
    integer_range = range_field(number, as_integer_range, 'integer_range')
    return integer_range + Optional(pricing())


def decimal_range_field() -> ParserElement:
    """ Returns a decimal range parser. """

    number = Combine(Optional('-') + numeric + Literal('.') + numeric)
    return range_field(number, as_decimal_range, 'decimal_range')


def currency() -> ParserElement:
    """ Returns a currency parser.

    For example:

        chf
        USD
        Cny

    """

    return Regex(r'[a-zA-Z]{3}').set_parse_action(as_uppercase)('currency')


def pricing() -> ParserElement:
    """ Returns a pricing parser.

    For example:
        (10.0 CHF)
        (0 usd!)
        (-0.50 Cny)
    """

    cc_payment = Literal('!').set_parse_action(matches('!'))
    cc_payment = Optional(cc_payment, default=False)('credit_card_payment')

    pricing = Group(
        enclosed_in(decimal() + currency() + cc_payment, '()')
    )('pricing')
    return pricing


def discount() -> ParserElement:
    """ Returns a discount parser.

    For example:
        (100%)
        (-25 %)
        (33.3%)
    """

    return Group(
        enclosed_in(decimal() + Suppress('%'), '()')
    )('discount')


def marker_box(characters: str) -> ParserElement:
    """ Returns a marker box:

    Example::

        (x) Male
        [x] Female
        {x} What?
    """

    check = mark_enclosed_in(characters)('checked')
    pricing_or_discount_parser = pricing() | discount()
    # NOTE: This ended up being a nightmare to build with pyparsing primitives
    #       so I just gave up and used pure Regex, they use a lot of Regex
    #       internally anyways, so it should be fine. This required lazy
    #       matching, which makes this probably a bit slower than it could be
    #       but otherwise it should be equivalent to what we had before in
    #       what kind of characters are allowed to be used in labels.
    #       It might be possible to implement this using left recursion in
    #       pyparsing, but it seemed just as difficult as with right recursion
    #       since the label will still fundamentally act greedily. I couldn't
    #       find any pyparsing native way to make it lazy instead.
    #       If pricing wasn't optional this would be easy...
    pricing_re = r'*[(] *-?[0-9]+(?:\.[0-9]+)? *(?:%|[A-Za-z]{3}!?) *[)]'
    label = Regex(
        # a sequence of words (that can't start with brackets)
        rf'(?P<label>{text_without_re(characters + "()")}(?: ?{word_re})*?)'
        # followed by optional pricing or discount followed by end of line or
        # multiple spaces
        rf'(?= *$| *{no_printable_or_whitespace_re}| {pricing_re}|  )'
    )
    return check + label + Optional(pricing_or_discount_parser)


def radio() -> ParserElement:
    """ Returns a radio parser:

    Example::
        (x) Male
        ( ) Female
    """
    return marker_box('()').set_parse_action(tag(type='radio'))


def checkbox() -> ParserElement:
    """ Returns a checkbox parser:

    Example::
        [x] Male
        [ ] Female
    """
    return marker_box('[]').set_parse_action(tag(type='checkbox'))


def fieldset_title() -> ParserElement:
    """ A fieldset title parser. Fieldset titles are just like headings in
    markdown::

        # My header

    It's possible to have an empty fieldset title (to disable a fieldset):

        # ...

    """

    label = with_whitespace_inside(text).set_results_name('label')

    fieldset_title = Suppress('#') + (Suppress('...') | label)
    fieldset_title = fieldset_title.set_parse_action(tag(type='fieldset'))

    return fieldset_title


def field_identifier() -> ParserElement:
    """ Returns a field identifier parser:

    Example::

        My field *

    """

    required = Literal('*').set_parse_action(matches('*'))
    required = Optional(required, default=False)('required')

    # a field name can contain any kind of character, except for a '=' and
    # a '*', which we'll need later for the field definition
    characters = with_whitespace_inside(text_without('*='))
    label = Combine(OneOrMore(characters))('label')

    # a field declaration begins with spaces (so we can differentiate between
    # text and catual fields), then includes the name and the '*' which marks
    # required fields
    return label + required + Suppress('=')


def field_help_identifier() -> ParserElement:
    """ Returns parser for a field help comment following a field/fieldset:

    General Example:

        << Help text for My Field >>

    """
    field_explanation = with_whitespace_inside(text_without('>'))('message')
    return Suppress('<<') + field_explanation + Suppress('>>')
