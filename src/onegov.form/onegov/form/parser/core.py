from onegov.form.core import (
    Form,
    with_options
)
from onegov.form.fields import MultiCheckboxField
from onegov.form.utils import label_to_field_id
from onegov.form.parser.grammar import document
from wtforms import (
    PasswordField,
    RadioField,
    StringField,
    TextAreaField
)
from wtforms.fields.html5 import EmailField
from wtforms_components import If
from wtforms.widgets import TextArea
from wtforms.validators import InputRequired, Length


# cache the parser
doc = document()


def parse_form(text):
    """ Takes the given form text, parses it and returns a WTForms form
    class (not an instance of it).

    """

    builder = WTFormsClassBuilder(Form)

    for block in (i[0] for i in doc.scanString(text)):
        handle_block(builder, block)

    return builder.form_class


def handle_block(builder, block, dependency=None):
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
