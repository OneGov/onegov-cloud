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

Date
~~~~

A date (without time) is defined by this exact string: ``YYYY.MM.DD``::

    I'm a date field = YYYY.MM.DD

Note that this doesn't mean that the date format can be influenced.

Datetime
~~~~~~~~

A date (with time) is defined by this exact string: ``YYYY.MM.DD HH:MM``::

    I'm a datetime field = YYYY.MM.DD HH:MM

Again, this doesn't mean that the datetime format can be influenced.

Time
~~~~

A Time is defined by this exact string: ``HH:MM``::

    I'm a time field = HH:MM

One more time, this doesn't mean that the datetime format can be influenced.

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
form can be modeled:

    Node Size =
        ( ) Small (20 USD)
        (x) Medium (30 USD)
        ( ) Large (40 USD)

    Extras =
        [x] Second IP Address (20 CHF)
        [x] Backup (20 CHF)

The additional pricing metadata can be used to provide simple order forms.
As in any other form, dependencies are taken into account.

"""

import pyparsing as pp
import yaml

from html import escape
from onegov.core.utils import Bunch
from onegov.form.core import (
    FieldDependency,
    Form,
    with_options
)
from onegov.form import errors
from onegov.form.fields import MultiCheckboxField, UploadField
from onegov.form.parser.grammar import (
    checkbox,
    date,
    datetime,
    email,
    field_identifier,
    fieldset_title,
    fileinput,
    password,
    radio,
    stdnum,
    textarea,
    textfield,
    time,
)
from onegov.form.utils import label_to_field_id
from onegov.form.validators import (
    Stdnum, ExpectedExtensions, FileSizeLimit, WhitelistedMimeType
)
from wtforms import (
    PasswordField,
    RadioField,
    StringField,
    TextAreaField
)
from wtforms.fields.html5 import DateField, DateTimeLocalField, EmailField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea
from wtforms_components import Email, If, TimeField


# cache the parser elements
elements = Bunch()
elements.identifier = field_identifier()
elements.fieldset_title = fieldset_title()
elements.textfield = textfield()
elements.textarea = textarea()
elements.password = password()
elements.email = email()
elements.stdnum = stdnum()
elements.datetime = datetime()
elements.date = date()
elements.time = time()
elements.fileinput = fileinput()
elements.radio = radio()
elements.checkbox = checkbox()
elements.boxes = elements.checkbox | elements.radio
elements.single_line_fields = elements.identifier + pp.MatchFirst([
    elements.textfield,
    elements.textarea,
    elements.password,
    elements.email,
    elements.stdnum,
    elements.datetime,
    elements.date,
    elements.time,
    elements.fileinput
])


# increasing the default filesize is *strongly discouarged*, as we are not
# storing those files in the database, so they need to fit in memory
#
# if this value must be higher, we need to store the files outside the
# database
#
MEGABYTE = 1000 ** 2
DEFAULT_UPLOAD_LIMIT = 5 * MEGABYTE


class CustomLoader(yaml.SafeLoader):
    """ Extends the default yaml loader with customized constructors. """


class constructor(object):
    """ Adds decorated functions to as constructors to the CustomLoader. """

    def __init__(self, tag):
        self.tag = tag

    def __call__(self, fn):
        CustomLoader.add_constructor(self.tag, fn)
        return fn


@constructor('!text')
def construct_textfield(loader, node):
    return elements.textfield.parseString(node.value)


@constructor('!textarea')
def construct_textarea(loader, node):
    return elements.textarea.parseString(node.value)


@constructor('!email')
def construct_email(loader, node):
    return elements.email.parseString(node.value)


@constructor('!stdnum')
def construct_stdnum(loader, node):
    return elements.stdnum.parseString(node.value)


@constructor('!date')
def construct_date(loader, node):
    return elements.date.parseString(node.value)


@constructor('!datetime')
def construct_datetime(loader, node):
    return elements.datetime.parseString(node.value)


@constructor('!time')
def construct_time(loader, node):
    return elements.time.parseString(node.value)


@constructor('!radio')
def construct_radio(loader, node):
    return elements.radio.parseString(node.value)


@constructor('!checkbox')
def construct_checkbox(loader, node):
    return elements.checkbox.parseString(node.value)


@constructor('!fileinput')
def construct_fileinput(loader, node):
    return elements.fileinput.parseString(node.value)


@constructor('!password')
def construct_password(loader, node):
    return elements.password.parseString(node.value)


def parse_form(text, base_class=Form):
    """ Takes the given form text, parses it and returns a WTForms form
    class (not an instance of it).

    """

    builder = WTFormsClassBuilder(base_class)
    parsed = yaml.load('\n'.join(translate_to_yaml(text)), CustomLoader)

    for fieldset in parsed:

        # fieldsets occur only at the top level
        fieldset_name = next(k for k in fieldset.keys())

        if fieldset_name != '...':
            builder.set_current_fieldset(fieldset_name)
        else:
            builder.set_current_fieldset(None)

        for block in fieldset[fieldset_name]:
            handle_block(builder, block)

    form_class = builder.form_class
    form_class._source = text

    return form_class


def format_pricing(pricing):
    if not pricing:
        return ''

    return ' ({:.2f} {})'.format(pricing[0], pricing[1])


def handle_block(builder, block, dependency=None):
    """ Takes the given parsed yaml block and adds it to the from builder. """

    key, field = next(i for i in block.items())

    identifier_src = key.rstrip('= ') + '='
    identifier = elements.identifier.parseString(identifier_src)

    # add the nested options/dependencies in case of radio/checkbox buttons
    if isinstance(field, list):
        choices = [next(i for i in f.items()) for f in field]

        for choice, dependencies in choices:
            choice.dependencies = dependencies

        choices = [c[0] for c in choices]

        field = Bunch(choices=choices, type=choices[0].type)

        # make sure only one type is found (either radio or checkbox)
        types = set(f.type for f in field.choices)
        assert types <= {'radio', 'checkbox'}
        assert len(types) == 1

    if field.type == 'text':
        if field.length:
            validators = [Length(max=field.length)]
        else:
            validators = []

        field_id = builder.add_field(
            field_class=StringField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
            validators=validators,
        )
    elif field.type == 'textarea':
        field_id = builder.add_field(
            field_class=TextAreaField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
            widget=with_options(TextArea, rows=field.rows or None)
        )
    elif field.type == 'password':
        field_id = builder.add_field(
            field_class=PasswordField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required
        )
    elif field.type == 'email':
        field_id = builder.add_field(
            field_class=EmailField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
            validators=[Email()]
        )
    elif field.type == 'stdnum':
        field_id = builder.add_field(
            field_class=StringField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
            validators=[Stdnum(field.format)]
        )
    elif field.type == 'date':
        field_id = builder.add_field(
            field_class=DateField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
        )
    elif field.type == 'datetime':
        field_id = builder.add_field(
            field_class=DateTimeLocalField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
        )
    elif field.type == 'time':
        field_id = builder.add_field(
            field_class=TimeField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required
        )
    elif field.type == 'fileinput':
        field_id = builder.add_field(
            field_class=UploadField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
            validators=[
                WhitelistedMimeType(),
                ExpectedExtensions(field.extensions),
                FileSizeLimit(DEFAULT_UPLOAD_LIMIT)
            ]
        )
    elif field.type == 'radio':
        choices = [
            (c.label, c.label + format_pricing(c.pricing))
            for c in field.choices
        ]
        checked = [c.label for c in field.choices if c.checked]
        default = checked and checked[0] or None

        pricing = {c.label: c.pricing for c in field.choices if c.pricing}

        field_id = builder.add_field(
            field_class=RadioField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
            choices=choices,
            default=default,
            pricing=pricing or None
        )
    elif field.type == 'checkbox':
        choices = [
            (c.label, c.label + format_pricing(c.pricing))
            for c in field.choices
        ]
        default = [c.label for c in field.choices if c.checked]

        pricing = {c.label: c.pricing for c in field.choices if c.pricing}

        field_id = builder.add_field(
            field_class=MultiCheckboxField,
            label=identifier.label,
            dependency=dependency,
            required=identifier.required,
            choices=choices,
            default=default,
            pricing=pricing or None
        )
    else:
        raise NotImplementedError

    # go through nested blocks and recursively add them
    if field.type in {'radio', 'checkbox'}:
        for choice in field.choices:
            if not choice.dependencies:
                continue

            dependency = FieldDependency(field_id, choice.label)

            for child in choice.dependencies:
                handle_block(builder, child, dependency)

    return field_id


def match(expr, text):
    """ Returns true if the given parser expression matches the given text. """
    try:
        expr.parseString(text)
    except pp.ParseException:
        return False
    else:
        return True


def try_parse(expr, text):
    """ Returns the result of the given parser expression and text, or None.

    """
    try:
        return expr.parseString(text)
    except pp.ParseException:
        return None


def prepare(text):
    """ Takes the raw form source and prepares it for the translation into
    yaml.

    """

    lines = (l.rstrip() for l in text.split('\n'))
    lines = ((ix, l) for ix, l in enumerate(lines) if l)
    lines = ((ix, l) for ix, l in ensure_a_fieldset(lines))

    for line in lines:
        yield line


def ensure_a_fieldset(lines):
    """ Makes sure that the given lines all belong to a fieldset. That means
    adding an empty fieldset before all lines, if none is found first.

    """
    found_fieldset = False

    for ix, line in lines:
        if found_fieldset:
            yield ix, line
            continue

        if match(elements.fieldset_title, line):
            found_fieldset = True
            yield ix, line
        else:
            found_fieldset = True
            yield -1, '# ...'
            yield ix, line


def translate_to_yaml(text):
    """ Takes the given form text and constructs an easier to parse yaml
    string.

    """

    lines = ((ix, l) for ix, l in prepare(text))
    expect_nested = False
    actual_fields = 0

    for ix, line in lines:

        indent = ' ' * (4 + (len(line) - len(line.lstrip())))

        # the top level are the fieldsets
        if match(elements.fieldset_title, line):
            yield '- "{}":'.format(line.lstrip('# ').rstrip())
            expect_nested = False
            continue

        # fields are nested lists of dictionaries
        parse_result = try_parse(elements.single_line_fields, line)
        if parse_result is not None:
            yield '{indent}- "{identifier}": !{type} "{definition}"'.format(
                indent=indent,
                type=parse_result.type,
                identifier=line.split('=')[0].strip(),
                definition=line.split('=')[1].strip()
            )
            expect_nested = len(indent) > 4
            actual_fields += 1
            continue

        # checkboxes/radios come without identifier
        parse_result = try_parse(elements.boxes, line)
        if parse_result is not None:

            if not expect_nested:
                raise errors.InvalidFormSyntax(line=ix + 1)

            yield '{indent}- !{type} "{definition}":'.format(
                indent=indent,
                type=parse_result.type,
                definition=line.strip()
            )
            continue

        # identifiers which are alone contain nested checkboxes/radios
        if match(elements.identifier, line):

            # this should have been matched by the single line field above
            if not line.endswith('='):
                raise errors.InvalidFormSyntax(line=ix + 1)

            yield '{indent}- "{identifier}":'.format(
                indent=indent,
                identifier=line.strip()
            )

            expect_nested = True
            actual_fields += 1
            continue

        raise errors.InvalidFormSyntax(line=ix + 1)

    if not actual_fields:
        raise errors.InvalidFormSyntax(line=ix + 1)


class WTFormsClassBuilder(object):
    """ Helps dynamically build a wtforms class from parsed blocks.

    For example::

        builder = WTFormsClassBuilder(BaseClass)
        builder.add_field(StringField, label='Name', required=True)

        MyForm = builder.form_class
    """

    def __init__(self, base_class):

        class DynamicForm(base_class):
            pass

        self.form_class = DynamicForm
        self.current_fieldset = None

    def set_current_fieldset(self, label):
        self.current_fieldset = label

    def validators_extend(self, validators, required, dependency):
        if required:
            if dependency is None:
                self.validators_add_required(validators)
            else:
                self.validators_add_dependency(validators, dependency)
        else:
            self.validators_add_optional(validators)

    def validators_add_required(self, validators):
        # we use the DataRequired check instead of InputRequired, since
        # InputRequired only works if the data comes over the wire. We
        # also want to load forms with data from the database, where
        # InputRequired will fail, but DataRequired will not.
        #
        # As a consequence, falsey values can't be submitted for now.
        validators.insert(0, DataRequired())

    def validators_add_dependency(self, validators, dependency):
        # set the requried flag, even if it's not always required
        # as it's better to show it too often, than not often enough
        validator = If(dependency.fulfilled, DataRequired())
        validator.field_flags = ('required', )
        validators.insert(0, validator)

    def validators_add_optional(self, validators):
        validators.insert(0, Optional())

    def mark_as_dependent(self, field_id, dependency):
        field = getattr(self.form_class, field_id)
        widget = field.kwargs.get('widget', field.field_class.widget)

        field.kwargs['widget'] = with_options(
            widget, **dependency.html_data
        )

    def get_unique_field_id(self, label, dependency):
        # try to find a smart field_id that contains the dependency or the
        # current fieldset name - if all fails, an error will be thrown,
        # as field_ids *need* to be unique
        if dependency:
            field_id = dependency.field_id + '_' + label_to_field_id(label)
        elif self.current_fieldset:
            field_id = label_to_field_id(self.current_fieldset + ' ' + label)
        else:
            field_id = label_to_field_id(label)

        if hasattr(self.form_class, field_id):
            raise errors.DuplicateLabelError(label=label)

        return field_id

    def add_field(self, field_class, label, required,
                  dependency=None, field_id=None, pricing=None, **kwargs):
        validators = kwargs.pop('validators', [])

        # labels in wtforms are not escaped correctly - for safety we make sure
        # that the label is properly html escaped. See also:
        # https://github.com/wtforms/wtforms/issues/315
        # -> quotes are allowed because the label is rendered between tags,
        # not as part of the attributes
        label = escape(label, quote=False)
        field_id = field_id or self.get_unique_field_id(label, dependency)

        self.validators_extend(validators, required, dependency)

        setattr(self.form_class, field_id, field_class(
            label=label,
            validators=validators,
            fieldset=self.current_fieldset,
            pricing=pricing,
            **kwargs
        ))

        if dependency:
            self.mark_as_dependent(field_id, dependency)

        return field_id
