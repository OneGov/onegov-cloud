# -*- coding: utf-8 -*-
from onegov.form.compat import unicode_characters
from pyparsing import (
    nums,
    Combine,
    Group,
    Literal,
    OneOrMore,
    Optional,
    StringEnd,
    Suppress,
    Word,
    White,
    ZeroOrMore
)


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


def unwrap(tokens):
    return tokens[0][0]


def tag(**tags):
    def apply_tags(tokens):
        for key, value in tags.items():
            tokens[key] = value
    return apply_tags


def field_declaration():
    """ Returns a field declaration parser:

    Example:
        My field * =

    """

    required = Literal('*').setParseAction(matches('*'))

    # a field name can contain any kind of character, except for a '=' and
    # a '*', which we'll need later for the field definition
    characters = text_without('*=') | White(max=1) + text_without('*=')
    label = Combine(OneOrMore(characters))

    # a field declaration begins with spaces (so we can differentiate between
    # text and catual fields), then includes the name and the '*' which marks
    # required fields
    field_declaration = label.setResultsName('label')
    field_declaration += Optional(required).setResultsName('required')
    field_declaration += Suppress('=')

    return field_declaration


def textfield():
    """ Returns a textfield parser.

    Example:
        ____[50]

    """
    textfield_length = Suppress('[') + numeric + Suppress(']')
    textfield_length = textfield_length.setParseAction(as_int)
    textfield_length = textfield_length.setResultsName('length')

    textfield = Literal('___') + Optional(textfield_length)
    textfield = textfield.setParseAction(tag(type='text'))

    return textfield


def textarea():
    """ Returns a textarea parser.

    Example:

        ...[100*4]

    """

    rows = Optional(Suppress('*') + numeric)('rows').setParseAction(as_int)
    cols = numeric('cols').setParseAction(as_int)

    dimension = Suppress('[') + cols + rows + Suppress(']')

    textarea = Literal('...') + Optional(dimension)
    textarea = textarea.setParseAction(tag(type='textarea'))

    return textarea


def password():
    """ Returns a password field parser.

    Example:
        ***

    """

    return Literal('***').setParseAction(tag(type='password'))


def radio_buttons():
    """ Returns a radio buttons parser.

    Example:
        () Male (x) Female
    """
    radio_button = Group(
        Literal('(x)').setParseAction(literal(True)) |
        Literal('()').setParseAction(literal(False))
    ).setResultsName('checked').setParseAction(unwrap)

    radio_button_text = Group(text + (~Literal('()') | ~Literal('(x)')))
    radio_button_text = radio_button_text.setResultsName('label')
    radio_button_text = radio_button_text.setParseAction(unwrap)

    radio_buttons = OneOrMore(Group(radio_button + radio_button_text))
    radio_buttons = radio_buttons.setParseAction(tag(type='radio'))

    return radio_buttons


def checkboxes():
    """ Returns a check boxes parser.

    Example:
        [] Android [x] iPhone [x] Blackberry

    """
    checkbox = Group(
        Literal('[x]').setParseAction(literal(True)) |
        Literal('[]').setParseAction(literal(False))
    ).setResultsName('checked').setParseAction(unwrap)

    checkbox_text = Group(text + (~Literal('[]') | ~Literal('[x]')))
    checkbox_text = checkbox_text.setResultsName('label')
    checkbox_text = checkbox_text.setParseAction(unwrap)

    checkboxes = OneOrMore(Group(checkbox + checkbox_text))
    checkboxes = checkboxes.setParseAction(tag(type='checkbox'))

    return checkboxes


def select():
    """ Returns a select parser.

    Examples:
        {ZRH, KUL, (DXB)}
        {ZRH > Zürich, KUL > Kuala Lumpur, (DXB > Dubai)}

    The parentheses identify the selected element.

    """
    key = text_without('(){},>').setResultsName('key')
    label = text_without('(){},>').setResultsName('label')

    item = Optional(key + Suppress('>')) + label
    selected_item = Suppress('(') + item.copy() + Suppress(')')

    item.setParseAction(tag(selected=False))
    selected_item.setParseAction(tag(selected=True))

    item = Group(selected_item | item)
    items = item + ZeroOrMore(Suppress(',') + item)

    select = Suppress('{') + items + Suppress('}')
    select.setParseAction(tag(type='select'))

    return select


def fieldset_title():
    """ A fieldset title parser. Fieldset titles are just like headings in
    markdown:

        # My header

    It's possible to have an empty fieldset title (to disable a fieldset):

        #

    """

    label = Combine(ZeroOrMore(text | White())).setResultsName('label')

    fieldset_title = Suppress('#') + label
    fieldset_title = fieldset_title.setParseAction(tag(type='fieldset'))

    return fieldset_title


# put together the actual grammar
fields = Group(
    textfield() |
    radio_buttons() |
    checkboxes() |
    select() |
    password() |
    textarea()
)

field = field_declaration() + fields.setResultsName('field')
field = field.setParseAction(tag(type='field'))

line = (fieldset_title() | field) + StringEnd()
