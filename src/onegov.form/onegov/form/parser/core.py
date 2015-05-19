from onegov.form.core import (
    Form,
    with_options
)
from onegov.form.utils import label_to_field_id
from onegov.form.parser.grammar import document
from wtforms import PasswordField, StringField, TextAreaField
from wtforms.widgets import TextArea
from wtforms.validators import InputRequired, Length


# cache the parser
doc = document()


def parse_form(text, custom_fields={}):
    """ Takes the given form text, parses it and returns a WTForms form
    class (not an instance of it).

    """

    builder = WTFormsClassBuilder(Form)

    for block in (i[0] for i in doc.scanString(text)):

        if block.type == 'fieldset':
            builder.set_current_fieldset(block.label or None)

        elif block.type == 'text':
            if block.length:
                validators = [Length(max=block.length)]
            else:
                validators = []

            builder.add_field(
                field_class=StringField,
                label=block.label,
                required=block.required,
                validators=validators
            )

        elif block.type == 'textarea':
            builder.add_field(
                field_class=TextAreaField,
                label=block.label,
                required=block.required,
                widget=with_options(TextArea, rows=block.rows or None)
            )
        elif block.type == 'password':
            builder.add_field(
                field_class=PasswordField,
                label=block.label,
                required=block.required
            )
        elif block.type == 'custom':
            if block.custom_id in custom_fields:
                builder.add_field(
                    field_class=custom_fields[block.custom_id],
                    label=block.label,
                    required=block.required
                )
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    return builder.form_class


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

    def add_field(self, field_class, label, required, **kwargs):
        validators = kwargs.pop('validators', [])

        if required:
            validators.insert(0, InputRequired())

        field_id = label_to_field_id(label)

        setattr(self.form_class, field_id, field_class(
            label=label,
            validators=validators,
            fieldset=self.current_fieldset,
            **kwargs
        ))
