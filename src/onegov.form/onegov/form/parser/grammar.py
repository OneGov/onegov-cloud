# -*- coding: utf-8 -*-
from onegov.form.compat import unicode_characters
from pyparsing import (
    col,
    nums,
    Combine,
    Forward,
    Group,
    indentedBlock,
    LineEnd,
    Literal,
    OneOrMore,
    Optional,
    ParserElement,
    MatchFirst,
    Suppress,
    Word,
    White,
)


# we want newlines to be significant
ParserElement.setDefaultWhitespaceChars(' \t')

text = Word(unicode_characters)
numeric = Word(nums)

# shortcut
indented = indentedBlock


block = Forward()


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

    Example:
        ____[50]

    The number defines the maximum length.

    """
    length = number_enclosed_in('[]')('length')

    textfield = Suppress('___') + Optional(length)
    textfield.setParseAction(tag(type='text'))

    return textfield


def textarea():
    """ Returns a textarea parser.

    Example:

        ...[5]

    The number defines the number of rows.

    """

    rows = number_enclosed_in('[]')('rows')

    textarea = Suppress('...') + Optional(rows)
    textarea.setParseAction(tag(type='textarea'))

    return textarea


def password():
    """ Returns a password field parser.

    Example:
        ***

    """

    return Suppress('***').setParseAction(tag(type='password'))


class Stack(list):

    def init(self, string, line, tokens):
        self[:] = [col(line, string) + 3]


def marker_box(characters, indent_stack=None):
    """ Returns a marker box:

    Example:
        (x) Male
        [x] Female
        {x} What?
    """

    check = mark_enclosed_in(characters)('checked')
    label = with_whitespace_inside(text_without(characters))('label')

    stack = Stack()
    check.setParseAction(stack.init)

    dependencies = Group(indented(block, stack))('dependencies')
    dependencies.setParseAction(unwrap)

    return Group(check + label + Optional(dependencies))


def radios():
    """ Returns a radio buttons parser.

    Example:
        ( ) Male (x) Female ( ) Space Alien
    """

    return OneOrMore(marker_box('()')).setParseAction(tag(type='radio'))


def checkboxes():
    """ Returns a check boxes parser.

    Example:
        [] Android [x] iPhone [x] Dumb Phone

    """
    boxes = OneOrMore(marker_box('[]'))
    boxes.setParseAction(tag(type='checkbox'))

    return boxes


def custom():
    """ Returns a custom field parser.

    Examples:
        /E-Mail
        /Stripe

    """

    custom_id = OneOrMore(text)('custom_id')
    custom_id.setParseAction(lambda t: t[0].lower())

    custom = Suppress('/') + custom_id
    custom.setParseAction(tag(type='custom'))

    return custom


def button():
    """ Returns a buttons parser.

    Examples:
        [Send]
        [Send](http://my-post-address.com)

    By default, buttons post to the form.

    """

    characters = with_whitespace_inside(text_without('[]'))

    label = Combine(OneOrMore(characters))('label')
    label.setParseAction(lambda t: t[0])

    url = OneOrMore(text_without('()'))('url').setParseAction(lambda t: t[0])

    button = Suppress('[') + label + Suppress(']')
    button += Optional(Suppress('(') + url + Suppress(')'))
    button.setParseAction((tag(type='button')))

    return button


def fieldset_title():
    """ A fieldset title parser. Fieldset titles are just like headings in
    markdown:

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

    Example:
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


def block_content():
    """ Returns the content of one logical parser block, this is the last
    step towards the document, which is a collection of these blocks.

    """
    LE = Suppress(LineEnd())
    identifier = field_identifier()

    return MatchFirst([
        button(),
        fieldset_title(),
        identifier + (textfield() | textarea() | password() | custom()),
        identifier + OneOrMore(Optional(LE) + radios())('parts'),
        identifier + OneOrMore(Optional(LE) + checkboxes())('parts')
    ])


def document():
    """ Returns a form document. """
    return OneOrMore(block_content())


block << block_content()
