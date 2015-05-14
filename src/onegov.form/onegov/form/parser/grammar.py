# -*- coding: utf-8 -*-
from onegov.form.compat import unicode_characters
from pyparsing import (
    nums,
    CharsNotIn,
    Combine,
    FollowedBy,
    Group,
    indentedBlock,
    LineEnd,
    LineStart,
    Literal,
    OneOrMore,
    Optional,
    ParserElement,
    MatchFirst,
    StringEnd,
    Suppress,
    Word,
    White,
    ZeroOrMore
)


# we want newlines to be significant
ParserElement.setDefaultWhitespaceChars(' \t')

text = Word(unicode_characters)
numeric = Word(nums)


def text_without(characters):
    return Word(unicode_characters, excludeChars=characters)


def matches(character):
    return lambda tokens: tokens and tokens[0] == character


def literal(text):
    return lambda tokens: text


def as_int(tokens):
    return int(tokens[0]) if tokens else None


def rstrip(tokens):
    return tokens[0].rstrip()


def unwrap(tokens):
    return tokens[0][0]


def tag(**tags):
    def apply_tags(tokens):
        for key, value in tags.items():
            tokens[key] = value
    return apply_tags


def with_whitespace_inside(expr):
    return expr | White(' ', max=1) + expr


def enclosed_in(expr, characters):
    left, right = characters
    return Suppress(left) + expr + Suppress(right)


def number_enclosed_in(characters):
    left, right = characters
    return enclosed_in(numeric, characters).setParseAction(as_int)


def mark_enclosed_in(characters):
    left, right = characters
    return MatchFirst((
        Literal(left + 'x' + right).setParseAction(literal(True)),
        Literal(left + ' ' + right).setParseAction(literal(False)),
        Literal(left + right).setParseAction(literal(False))
    ))


def textfield():
    """ Returns a textfield parser.

    Example:
        ____[50]

    The number defines the maximum length.

    """
    length = number_enclosed_in('[]')('length')

    textfield = Suppress('___') + Optional(length)
    textfield = textfield.setParseAction(tag(type='text'))

    return textfield


def textarea():
    """ Returns a textarea parser.

    Example:

        ...[5]

    The number defines the number of rows.

    """

    rows = number_enclosed_in('[]')('rows')

    textarea = Suppress('...') + Optional(rows)
    textarea = textarea.setParseAction(tag(type='textarea'))

    return textarea


def password():
    """ Returns a password field parser.

    Example:
        ***

    """

    return Suppress('***').setParseAction(tag(type='password'))


def radios():
    """ Returns a radio buttons parser.

    Example:
        () Male (x) Female ( ) Space Alien
    """

    check = mark_enclosed_in('()')('checked')
    label = Combine(OneOrMore(CharsNotIn('()\n')))('label')
    label.setParseAction(rstrip)

    radios = OneOrMore(Group(check + label))
    radios.setParseAction(tag(type='radio'))

    return radios


def checkboxes():
    """ Returns a check boxes parser.

    Example:
        [] Android [x] iPhone [x] Dumb Phone

    """
    check = mark_enclosed_in('[]')('checked')
    characters = with_whitespace_inside(text_without('[]'))
    label = Combine(OneOrMore(characters))('label')

    return OneOrMore(Group(check + label)).setParseAction(tag(type='checkbox'))


def select():
    """ Returns a select parser.

    Examples:
        {ZRH, KUL, (DXB)}
        {ZRH > Zürich, KUL > Kuala Lumpur, (DXB > Dubai)}

    The parentheses identify the selected element.

    """
    chars = OneOrMore(with_whitespace_inside(text_without('(){},>')))

    key = Optional(chars + Suppress('>'))('key').setParseAction(
        lambda t: t and t[0] or None)

    unselected = key + chars('label').setParseAction(lambda t: t[0])
    selected = enclosed_in(unselected, '()').setParseAction(tag(selected=True))

    unselected.setParseAction(tag(selected=False))
    selected.setParseAction(tag(selected=True))

    item = Group(selected | unselected)
    items = item + ZeroOrMore(Suppress(',') + item)

    return enclosed_in(items, '{}').setParseAction(tag(type='select'))


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

    label = Combine(OneOrMore(CharsNotIn('\n'))).setResultsName('label')

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


def field_description():
    """ Returns the right hand side of the field definition. """
    return MatchFirst([
        textfield(),
        radios(),
        checkboxes(),
        select(),
        password(),
        textarea(),
        custom()
    ])


def indented(content):
    return indentedBlock(content, [1]).setParseAction(unwrap)


def block_content():
    LE = Suppress(LineEnd())
    identifier = field_identifier()

    return MatchFirst([
        button(),
        fieldset_title(),
        identifier + (textfield() | textarea() | password() | custom()),
        identifier + OneOrMore(Optional(LE) + radios())('parts'),
        identifier + OneOrMore(Optional(LE) + checkboxes())('parts'),
        identifier + OneOrMore(Optional(LE) + select())('parts')
    ])


def document():
    return OneOrMore(block_content())

# defines a field on a single linge
# field_definition = field_identifier() + Suppress('=') + field_description()
# field_definition.setParseAction(tag(type='field'))
# field_definition = field_identifier() + field_description()

# block = Forward()
# block_content = field_definition | field_identifier() + block
# block << block_content | Optional(indentedBlock(block_content, [1]))
