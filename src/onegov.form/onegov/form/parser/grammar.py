from pyparsing import (
    alphanums,
    Combine,
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


def rstrip(tokens):
    """ Strips whitetext on the right of the token. """
    return tokens[0].rstrip()


def unwrap(tokens):
    """ Unwraps grouped tokens. """
    return tokens[0][0]


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

    """
    length = number_enclosed_in('[]')('length')

    textfield = Suppress('___') + Optional(length)
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


def marker_box(characters):
    """ Returns a marker box:

    Example::

        (x) Male
        [x] Female
        {x} What?
    """

    check = mark_enclosed_in(characters)('checked')
    label = with_whitespace_inside(text_without(characters))('label')

    return check + label


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
        [] ] Female
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
