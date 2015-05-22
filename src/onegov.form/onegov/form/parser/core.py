from onegov.form.core import (
    Form,
    with_options
)
from onegov.form.fields import TimeField, MultiCheckboxField
from onegov.form.parser.grammar import block_content
from onegov.form.utils import label_to_field_id
from onegov.form.validators import Stdnum
from wtforms import (
    PasswordField,
    RadioField,
    StringField,
    TextAreaField
)
from wtforms.fields.html5 import DateField, DateTimeLocalField, EmailField
from wtforms.validators import InputRequired, Length
from wtforms.widgets import TextArea
from wtforms_components import Email, If


# cache the parser
block_parser = block_content()


def parse_form(text):
    """ Takes the given form text, parses it and returns a WTForms form
    class (not an instance of it).

    """

    builder = WTFormsClassBuilder(Form)

    # XXX this is a bit of a hack, see method docs
    text = stress_indentations(text)

    for block in (i[0] for i in block_parser.scanString(text)):
        handle_block(builder, block)

    form_class = builder.form_class
    form_class._source = text

    return form_class


def stress_indentations(text):
    """ The parser's indent matching fails to detect indentations correctly,
    if there's no newline between an indeted part and and a dedented part.

    For example, this will fail:

        parent
            child
                grandchild
            sibling

    But this won't:

        parent
            child
                grandchild

            sibling

    Having tried a few things without success I want to move on for now, so
    to work around this issue, this function is called before the string
    is parsed, which fixes this issue.

    It does so by adding newlines after each dedent.

    """
    def lines_with_empty_lines_inserted(lines):
        previous_indentation = 0

        for line in lines:
            indentation = len(line) - len(line.lstrip())

            if previous_indentation > indentation:
                yield ''
                yield line
            else:
                yield line

            previous_indentation = indentation

    return '\n'.join(lines_with_empty_lines_inserted(text.split('\n')))


def handle_block(builder, block, dependency=None):
    """ Takes a parsed block and instructs the builder to add a field based
    on it.

    """

    if block.type == 'fieldset':
        builder.set_current_fieldset(block.label or None)
    elif block.type == 'text':
        if block.length:
            validators = [Length(max=block.length)]
        else:
            validators = []

        field_id = builder.add_field(
            field_class=StringField,
            label=block.label,
            dependency=dependency,
            required=block.required,
            validators=validators,
        )
    elif block.type == 'textarea':
        field_id = builder.add_field(
            field_class=TextAreaField,
            label=block.label,
            dependency=dependency,
            required=block.required,
            widget=with_options(TextArea, rows=block.rows or None)
        )
    elif block.type == 'password':
        field_id = builder.add_field(
            field_class=PasswordField,
            label=block.label,
            dependency=dependency,
            required=block.required
        )
    elif block.type == 'email':
        field_id = builder.add_field(
            field_class=EmailField,
            label=block.label,
            dependency=dependency,
            required=block.required,
            validators=[Email()]
        )
    elif block.type == 'stdnum':
        field_id = builder.add_field(
            field_class=StringField,
            label=block.label,
            dependency=dependency,
            required=block.required,
            validators=[Stdnum(block.format)]
        )
    elif block.type == 'date':
        field_id = builder.add_field(
            field_class=DateField,
            label=block.label,
            dependency=dependency,
            required=block.required,
        )
    elif block.type == 'datetime':
        field_id = builder.add_field(
            field_class=DateTimeLocalField,
            label=block.label,
            dependency=dependency,
            required=block.required,
        )
    elif block.type == 'time':
        field_id = builder.add_field(
            field_class=TimeField,
            label=block.label,
            dependency=dependency,
            required=block.required
        )
    elif block.type == 'radio':
        choices = [
            (c.label, c.label) for c in block.parts
        ]
        checked = [c.label for c in block.parts if c.checked]
        default = checked and checked[0] or None

        field_id = builder.add_field(
            field_class=RadioField,
            label=block.label,
            dependency=dependency,
            required=block.required,
            choices=choices,
            default=default
        )
    elif block.type == 'checkbox':
        choices = [
            (c.label, c.label) for c in block.parts
        ]
        default = [c.label for c in block.parts if c.checked]
        field_id = builder.add_field(
            field_class=MultiCheckboxField,
            label=block.label,
            dependency=dependency,
            required=block.required,
            choices=choices,
            default=default
        )
    else:
        raise NotImplementedError

    # go through nested blocks
    if block.type in {'radio', 'checkbox'}:
        for part in block.parts:
            dependency = FieldDependency(field_id, part.label)

            for child in part.dependencies:
                handle_block(builder, child, dependency)


class FieldDependency(object):
    """ Defines a dependency to a field. The given field must have the given
    choice for this dependency to be fulfilled.

    """

    def __init__(self, field_id, choice):
        self.field_id = field_id
        self.choice = choice

    def fulfilled(self, form, field):
        return getattr(form, self.field_id).data == self.choice

    @property
    def html_data(self):
        return {'data-depends-on': '/'.join((self.field_id, self.choice))}


class WTFormsClassBuilder(object):
    """ Helps dynamically build a wtforms class from parsed blocks.

    For example::

        builder = WTFormsClassBuilder(BaseClass)
        builder.add_field(StringField, label='Name', required=True)

        MyForm = builder.form_class
    """

    def __init__(self, form_class):

        class DynamicForm(form_class):
            pass

        self.form_class = DynamicForm
        self.current_fieldset = None

    def set_current_fieldset(self, label):
        self.current_fieldset = label

    def add_field(self, field_class, label, required,
                  dependency=None, **kwargs):
        validators = kwargs.pop('validators', [])

        if required:
            if dependency is None:
                validators.insert(0, InputRequired())
            else:
                validators.insert(0, If(dependency.fulfilled, InputRequired()))

        field_id = label_to_field_id(label)

        setattr(self.form_class, field_id, field_class(
            label=label,
            validators=validators,
            fieldset=self.current_fieldset,
            **kwargs
        ))

        if dependency:
            field = getattr(self.form_class, field_id)
            widget = field.kwargs.get('widget', field.field_class.widget)

            field.kwargs['widget'] = with_options(
                widget, **dependency.html_data
            )

        return field_id
