from html import escape
from onegov.form import errors
from onegov.form.core import FieldDependency
from onegov.form.core import Form
from onegov.form.core import with_options
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import UploadField
from onegov.form.parser.core import parse_formcode
from onegov.form.utils import label_to_field_id
from onegov.form.validators import ExpectedExtensions
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import Stdnum
from onegov.form.validators import WhitelistedMimeType
from wtforms import PasswordField
from wtforms import RadioField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.fields.html5 import DateField, DateTimeLocalField, EmailField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import TextArea
from wtforms_components import Email, If, TimeField


# increasing the default filesize is *strongly discouarged*, as we are not
# storing those files in the database, so they need to fit in memory
#
# if this value must be higher, we need to store the files outside the
# database
#
MEGABYTE = 1000 ** 2
DEFAULT_UPLOAD_LIMIT = 5 * MEGABYTE


def parse_form(text, base_class=Form):
    """ Takes the given form text, parses it and returns a WTForms form
    class (not an instance of it).

    """

    builder = WTFormsClassBuilder(base_class)

    for fieldset in parse_formcode(text):
        builder.set_current_fieldset(fieldset.label)

        for field in fieldset.fields:
            handle_field(builder, field)

    form_class = builder.form_class
    form_class._source = text

    return form_class


def handle_field(builder, field, dependency=None):
    """ Takes the given parsed field and adds it to the form. """

    if field.type == 'text':
        if field.maxlength:
            validators = [Length(max=field.maxlength)]
        else:
            validators = []

        builder.add_field(
            field_class=StringField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=validators
        )

    elif field.type == 'textarea':
        builder.add_field(
            field_class=TextAreaField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            widget=with_options(TextArea, rows=field.rows)
        )

    elif field.type == 'password':
        builder.add_field(
            field_class=PasswordField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required
        )

    elif field.type == 'email':
        builder.add_field(
            field_class=EmailField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[Email()]
        )

    elif field.type == 'stdnum':
        builder.add_field(
            field_class=StringField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[Stdnum(field.format)]
        )

    elif field.type == 'date':
        builder.add_field(
            field_class=DateField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
        )

    elif field.type == 'datetime':
        builder.add_field(
            field_class=DateTimeLocalField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
        )

    elif field.type == 'time':
        builder.add_field(
            field_class=TimeField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required
        )

    elif field.type == 'fileinput':
        builder.add_field(
            field_class=UploadField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[
                WhitelistedMimeType(),
                ExpectedExtensions(field.extensions),
                FileSizeLimit(DEFAULT_UPLOAD_LIMIT)
            ]
        )

    elif field.type == 'radio':
        builder.add_field(
            field_class=RadioField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            choices=[(c.key, c.label) for c in field.choices],
            default=next((c.key for c in field.choices if c.selected), None),
            pricing=field.pricing
        )

    elif field.type == 'checkbox':
        builder.add_field(
            field_class=MultiCheckboxField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            choices=[(c.key, c.label) for c in field.choices],
            default=[c.key for c in field.choices if c.selected],
            pricing=field.pricing
        )

    else:
        raise NotImplementedError

    if field.type in ('radio', 'checkbox'):
        for choice in field.choices:
            if not choice.fields:
                continue

            dependency = FieldDependency(field.id, choice.label)

            for choice_field in choice.fields:
                handle_field(builder, choice_field, dependency)


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

    def add_field(self, field_class, field_id, label, required,
                  dependency=None, pricing=None, **kwargs):
        validators = kwargs.pop('validators', [])

        if hasattr(self.form_class, field_id):
            raise errors.DuplicateLabelError(label=label)

        # labels in wtforms are not escaped correctly - for safety we make sure
        # that the label is properly html escaped. See also:
        # https://github.com/wtforms/wtforms/issues/315
        # -> quotes are allowed because the label is rendered between tags,
        # not as part of the attributes
        label = escape(label, quote=False)

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

        return getattr(self.form_class, field_id)
