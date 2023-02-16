import re

from datetime import date as dateobj
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from onegov.form.utils import decimal_range
from pyparsing import (
    alphanums,
    Combine,
    FollowedBy,
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


# we want newlines to be significant
ParserElement.setDefaultWhitespaceChars(' \t')

printables = pyparsing_unicode.Latin1.printables
text = Word(printables)
numeric = Word(nums)


def text_without(characters):
    """ Returns all printable text without the given characters. """
    return Word(printables, excludeChars=characters)


def matches(character):
    """ Returns true if the given character matches the token. """
    return lambda tokens: tokens and tokens[0] == character


def literal(text):
    """" Returns the given value, ignoring the tokens alltogether. """
    return lambda tokens: text


def as_int(tokens):
    """ Converts the token to int if possible. """
    return int(tokens[0]) if tokens else None


def as_joined_string(tokens):
    """ Joins the given tokens into a single string. """
    return ''.join(tokens[0])


def as_decimal(tokens):
    """ Converts the token to decimal if possible. """
    if tokens and tokens[0] == '-':
        tokens = tokens[1:]
        prefix = '-'
    else:
        prefix = '+'

    return Decimal(prefix + '.'.join(tokens)) if tokens else None


def as_uppercase(tokens):
    """ Converts the token to uppercase if possible. """
    return ''.join(tokens).upper() if tokens else None


def as_integer_range(tokens):
    """ Converts the token to an integer range if possible. """
    if tokens:
        return range(int(tokens[0]), int(tokens[1]))


def as_decimal_range(tokens):
    """ Converts the token to a decimal range if possible. """
    if tokens:
        return decimal_range(tokens[0], tokens[1])


def as_regex(tokens):
    """ Converts the token to a working regex if possible. """
    if tokens:
        return re.compile(tokens[0])


def as_date(instring, loc, tokens):
    """ Converts the token to a date if possible. """
    if not tokens:
        return
    try:
        return dateobj(int(tokens[0]), int(tokens[1]), int(tokens[2]))
    except ValueError:
        raise ParseFatalException(instring, loc, "Invalid date")


def approximate_total_days(delta):
    """ Computes an approximate day delta from a relativedelta. """
    return delta.years * 365.25 + delta.months * 30.5 + delta.days


def is_valid_date_range(instring, loc, tokens):
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

    raise ParseFatalException(instring, loc, "Invalid date range")


def as_relative_delta(tokens):
    if tokens:
        return relativedelta(**{tokens[1]: int(tokens[0])})


def unwrap(tokens):
    """ Unwraps grouped tokens. """

    if tokens:
        return tokens[0]


def tag(**tags):
    """ Takes the given tags and applies them to the token. """
    def apply_tags(tokens):
        for key, value in tags.items():
            tokens[key] = value
    return apply_tags


def with_whitespace_inside(expr):
    """ Returns an expression that allows for whitespace inside, but not
    outside the expression.

    """
    return Combine(OneOrMore(expr | White(' ', max=1) + expr))


def enclosed_in(expr, characters):
    """ Wraps the given expression in the given characters. """
    left, right = characters
    return Suppress(left) + expr + Suppress(right)


def number_enclosed_in(characters):
    """ Wraps numers in the given characters, making sure the result is an int.

    """
    left, right = characters
    return enclosed_in(numeric, characters).setParseAction(as_int)


def choices_enclosed_in(characters, choices):
    """ Wraps the given choices in the given characters, making sure only
    valid choices are possible.

    """
    choices = Regex(f'({"|".join(choices)})')
    return enclosed_in(choices, characters).setParseAction(unwrap)


def mark_enclosed_in(characters):
    """ Returns a mark (x) inclosed in the given characters. For example,
    ``mark_enclosed_in('[]')`` creates an expression that accepts any of these
    and sets the result of the 'x' value to True, the others to False::

        [x]
        [ ]
    """
    left, right = characters
    return MatchFirst((
        Literal(left + 'x' + right).setParseAction(literal(True)),
        Literal(left + ' ' + right).setParseAction(literal(False))
    ))


def textfield():
    """ Returns a textfield parser.

    Example::

        ____[50]

    The number defines the maximum length.

    Additionally, a regex may be specified to validate the field::

        ___/[0-9]{4}

    """
    length = number_enclosed_in('[]')('length')

    regex = Word(printables).setParseAction(as_regex)('regex')
    regex = Suppress('/') + regex

    textfield = Suppress('___') + Optional(length) + Optional(regex)
    textfield.setParseAction(tag(type='text'))

    return textfield


def textarea():
    """ Returns a textarea parser.

    Example::

        ...[5]

    The number defines the number of rows.

    """

    rows = number_enclosed_in('[]')('rows')

    textarea = Suppress('...') + Optional(rows)
    textarea.setParseAction(tag(type='textarea'))

    return textarea


def code():
    """ Returns a code textfield with a specified syntax.

    Currently only markdown is supported.

    Example::

        <markdown>

    """

    code = choices_enclosed_in('<>', ('markdown', ))('syntax')
    code.addParseAction(tag(type='code'))

    return code


def password():
    """ Returns a password field parser.

    Example::

        ***

    """

    return Suppress('***').setParseAction(tag(type='password'))


def email():
    """ Returns an email field parser.

    Example::

        @@@

    """
    return Suppress('@@@').setParseAction(tag(type='email'))


def url():
    """ Returns an url field parser.

    Example::

        http://
        https://

    """
    return Suppress(Regex(r'https?://')).setParseAction(tag(type='url'))


def absolute_date():
    """ Returns an absolute date parser.

    Example::

        2020.10.10
    """
    date_expr = numeric + Suppress('.') + numeric + Suppress('.') + numeric
    return date_expr.setParseAction(as_date)


def relative_delta():
    """ Returns a relative delta parser.

    Example::

        +1 days
        -4 weeks
        0 years
    """

    sign = Optional(Literal('-') | Literal('+'))
    grain = (Literal('days') | Literal('weeks') | Literal('months')
             | Literal('years'))
    return (Combine(sign + numeric) + grain).setParseAction(as_relative_delta)


def valid_date_range():
    """ Returns a valid date range parser.

    Example::

        (..today)
        (2010.01.01..2020.01.01)
        (-2 weeks..+4 months)

    """

    today = Literal('today').setParseAction(literal(relativedelta()))
    value_expr = Optional(
        today | relative_delta() | absolute_date(),
        default=None
    )
    date_range = value_expr('start') + Suppress('..') + value_expr('stop')
    date_range.setParseAction(is_valid_date_range)
    return Group(enclosed_in(date_range, '()'))('valid_date_range')


def date():
    """ Returns a date parser.

    Example::

        YYYY.MM.DD

    """

    date = Suppress('YYYY.MM.DD').setParseAction(tag(type='date'))
    return date + Optional(valid_date_range())


def datetime():
    """ Returns a datetime parser.

    Example::

        YYYY.MM.DD HH:MM

    """

    dt = Suppress('YYYY.MM.DD HH:MM').setParseAction(tag(type='datetime'))
    return dt + Optional(valid_date_range())


def time():
    """ Returns a time parser.

    Example::

        HH:MM

    """

    return Suppress('HH:MM').setParseAction(tag(type='time'))


def stdnum():
    """ Returns an stdnum parser.

    Example::

        # iban

    """
    prefix = Suppress('#') + Optional(White(" "))
    parser = prefix + Regex(r'[a-z\.]+')('format')
    parser.setParseAction(tag(type='stdnum'))

    return parser


def fileinput():
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

    def extract_file_types(tokens):
        if len(tokens) == 2 and tokens[1] == 'multiple':
            tokens['type'] = 'multiplefileinput'
        else:
            tokens['type'] = 'fileinput'

        if len(tokens[0]) == 0:
            tokens['extensions'] = ['*']
        else:
            tokens['extensions'] = [ext.lower() for ext in tokens[0].asList()]

    parser = extensions + Optional(multiple)
    parser.setParseAction(extract_file_types)

    return parser


def decimal():
    """ Returns a decimal parser.

    Decimal point is '.'.

    For example:

        0.00
        123
        11.1
        -10.0

    """

    return (Optional('-') + numeric + Optional(Suppress('.') + numeric))\
        .setParseAction(as_decimal)('amount')


def range_field(value_expression, parse_action, type):
    """ Generic range field parser. """

    r = (value_expression + Suppress('..') + value_expression)
    r = r.setParseAction(parse_action)
    r = r.addParseAction(tag(type=type))

    return r


def integer_range_field():
    """ Returns an integer range parser. """

    number = Combine(Optional('-') + numeric)
    integer_range = range_field(number, as_integer_range, 'integer_range')
    return integer_range + Optional(pricing())


def decimal_range_field():
    """ Returns a decimal range parser. """

    number = Combine(Optional('-') + numeric + Literal('.') + numeric)
    return range_field(number, as_decimal_range, 'decimal_range')


def currency():
    """ Returns a currency parser.

    For example:

        chf
        USD
        Cny

    """

    return Regex(r'[a-zA-Z]{3}').setParseAction(as_uppercase)('currency')


def pricing():
    """ Returns a pricing parser.

    For example:
        (10.0 CHF)
        (0 usd!)
        (-0.50 Cny)
    """

    cc_payment = Literal('!').setParseAction(matches('!'))
    cc_payment = Optional(cc_payment, default=False)('credit_card_payment')

    pricing = Group(
        enclosed_in(decimal() + currency() + cc_payment, '()')
    )('pricing')
    return pricing


def marker_box(characters):
    """ Returns a marker box:

    Example::

        (x) Male
        [x] Female
        {x} What?
    """

    check = mark_enclosed_in(characters)('checked')
    label_text = with_whitespace_inside(text_without(characters + '()'))
    pricing_parser = pricing()
    label = MatchFirst((
        label_text + FollowedBy(pricing_parser),
        Combine(label_text + with_whitespace_inside(text)),
        label_text
    )).setParseAction(as_joined_string)('label')

    return check + label + Optional(pricing_parser)


def radio():
    """ Returns a radio parser:

    Example::
        (x) Male
        ( ) Female
    """
    return marker_box('()').setParseAction(tag(type='radio'))


def checkbox():
    """ Returns a checkbox parser:

    Example::
        [x] Male
        [ ] Female
    """
    return marker_box('[]').setParseAction(tag(type='checkbox'))


def fieldset_title():
    """ A fieldset title parser. Fieldset titles are just like headings in
    markdown::

        # My header

    It's possible to have an empty fieldset title (to disable a fieldset):

        # ...

    """

    label = with_whitespace_inside(text).setResultsName('label')

    fieldset_title = Suppress('#') + (Suppress('...') | label)
    fieldset_title = fieldset_title.setParseAction(tag(type='fieldset'))

    return fieldset_title


def field_identifier():
    """ Returns a field identifier parser:

    Example::

        My field *

    """

    required = Literal('*').setParseAction(matches('*'))
    required = Optional(required, default=False)('required')

    # a field name can contain any kind of character, except for a '=' and
    # a '*', which we'll need later for the field definition
    characters = with_whitespace_inside(text_without('*='))
    label = Combine(OneOrMore(characters))('label')

    # a field declaration begins with spaces (so we can differentiate between
    # text and catual fields), then includes the name and the '*' which marks
    # required fields
    return label + required + Suppress('=')


def field_help_identifier():
    """ Returns parser for a field help comment following a field/fieldset:

    General Example:

        << Help text for My Field >>

    """
    field_explanation = with_whitespace_inside(text_without('>'))('message')
    return Suppress('<<') + field_explanation + Suppress('>>')
