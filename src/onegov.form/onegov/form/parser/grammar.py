# -*- coding: utf-8 -*-
""" onegov.form includes it's own markdownish form syntax, inspired by
https://github.com/maleldil/wmd

The goal of this syntax is to enable the creation of forms through the web,
without having to use javascript, html or python code.

Also, just like Markdown, we want this syntax to be readable by humans.

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
preselected::

    Gender = ( ) Female ( ) Male (x) I don't want to say

To improve readability, radio buttons may be listed on multiple lines, as
long as they are properly indented::

    Gender = ( ) Female
             ( ) Male
             (x) I don't want to say

Radio buttons also have the ability to define optional form parts. Those
parts are only shown if a question was answered a certain way.

Form parts are properly nested if they lign up with the label above them.

For example::

    Delivery Method = ( ) Pickup
                          Pickup Time = ___
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

    Extras = [x] Phone insurance
             [ ] Phone case
             [x] Extra battery

Just like radiobuttons, checkboxes may be nested to created dependencies::

    Additional toppings = [ ] Salami
                          [ ] Olives
                          [ ] Other
                              Description = ___

"""
from onegov.form.compat import unicode_characters
from pyparsing import (
    col,
    Combine,
    Forward,
    Group,
    indentedBlock,
    LineEnd,
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


def stdnum():
    """ Returns an stdnum parser.

    Example::

        # iban

    """
    prefix = Suppress('#') + Optional(White(" "))
    parser = prefix + Regex(r'[a-z\.]+')('format')
    parser.setParseAction(tag(type='stdnum'))

    return parser


class Stack(list):
    length_of_marker_box = 3

    def init(self, string, line, tokens):
        self[:] = [col(line, string) + self.length_of_marker_box]


def marker_box(characters):
    """ Returns a marker box:

    Example::

        (x) Male
        [x] Female
        {x} What?
    """

    check = mark_enclosed_in(characters)('checked')
    label = with_whitespace_inside(text_without(characters))('label')

    # Initialize the stack to the position of the label (which comes after
    # the checkbox), to get the correct indentation checks by pyparsing.
    stack = Stack()
    check.setParseAction(stack.init)

    dependencies = Group(indented(block, stack))('dependencies')
    dependencies.setParseAction(unwrap)

    return Group(check + label + Optional(dependencies))


def radios():
    """ Returns a radio buttons parser.

    Example::

        ( ) Male (x) Female ( ) Space Alien
    """

    return OneOrMore(marker_box('()')).setParseAction(tag(type='radio'))


def checkboxes():
    """ Returns a check boxes parser.

    Example::

        [] Android [x] iPhone [x] Dumb Phone

    """
    boxes = OneOrMore(marker_box('[]'))
    boxes.setParseAction(tag(type='checkbox'))

    return boxes


def custom():
    """ Returns a custom field parser.

    Examples::

        /E-Mail
        /Stripe

    """

    custom_id = OneOrMore(text)('custom_id')
    custom_id.setParseAction(lambda t: t[0].lower())

    custom = Suppress('/') + custom_id
    custom.setParseAction(tag(type='custom'))

    return custom


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


def block_content():
    """ Returns the content of one logical parser block, this is the last
    step towards the document, which is a collection of these blocks.

    """
    LE = Suppress(LineEnd())
    identifier = field_identifier()

    return MatchFirst([
        fieldset_title(),
        identifier + MatchFirst([
            textfield(),
            textarea(),
            password(),
            custom(),
            email(),
            stdnum()
        ]),
        identifier + OneOrMore(Optional(LE) + radios())('parts'),
        identifier + OneOrMore(Optional(LE) + checkboxes())('parts')
    ])


def document():
    """ Returns a form document. """
    return OneOrMore(block_content())


block << block_content()
