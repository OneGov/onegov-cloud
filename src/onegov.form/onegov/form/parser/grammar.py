import re

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
    OneOrMore,
    Optional,
    ParserElement,
    Regex,
    Suppress,
    White,
    Word,
)


# we want newlines to be significant
ParserElement.setDefaultWhitespaceChars(' \t')

unicode_characters = ''.join(
    chr(c) for c in range(65536) if not chr(c).isspace())
text = Word(unicode_characters)
numeric = Word(nums)


def text_without(characters):
    """ Returns all printable text without the given characters. """
    return Word(unicode_characters, excludeChars=characters)


def matches(character):
    """ Returns true if the given character matches the token. """
    return lambda tokens: tokens and tokens[0] == character


def literal(text):
    """" Returns the given value, ignoring the tokens alltogether. """
    return lambda tokens: text


def as_int(tokens):
    """ Converts the token to int if possible. """
    return int(tokens[0]) if tokens else None


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

    regex = Word(unicode_characters).setParseAction(as_regex)('regex')
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


def date():
    """ Returns a date parser.

    Example::

        YYYY.MM.DD

    """

    return Suppress('YYYY.MM.DD').setParseAction(tag(type='date'))


def datetime():
    """ Returns a datetime parser.

    Example::

        YYYY.MM.DD HH:MM

    """

    return Suppress('YYYY.MM.DD HH:MM').setParseAction(tag(type='datetime'))


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

    For specific files:
        *.pdf|*.doc
    """
    any_extension = Suppress('*.*')
    some_extension = Suppress('*.') + Word(alphanums) + Optional(Suppress('|'))

    def extract_file_types(tokens):
        tokens['type'] = 'fileinput'
        if len(tokens[0]) == 0:
            tokens['extensions'] = ['*']
        else:
            tokens['extensions'] = [ext.lower() for ext in tokens[0].asList()]

    parser = Group(any_extension | OneOrMore(some_extension))
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
    return range_field(number, as_integer_range, 'integer_range')


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


def marker_box(characters):
    """ Returns a marker box:

    Example::

        (x) Male
        [x] Female
        {x} What?
    """

    check = mark_enclosed_in(characters)('checked')
    pricing = enclosed_in(decimal() + currency(), '()')('pricing')

    label_text = with_whitespace_inside(text_without(characters + '()'))
    label = MatchFirst((
        label_text + FollowedBy(pricing),
        Combine(label_text + with_whitespace_inside(text)),
        label_text
    ))('label')

    return check + label + Optional(pricing)


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
