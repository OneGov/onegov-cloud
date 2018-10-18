import inspect
import phonenumbers

from onegov.core.html import sanitize_html
from onegov.core.utils import binary_to_dictionary
from onegov.file.utils import as_fileintent
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form.validators import ValidPhoneNumber
from onegov.form.widgets import IconWidget
from onegov.form.widgets import MultiCheckboxWidget
from onegov.form.widgets import OrderedMultiCheckboxWidget
from onegov.form.widgets import TagsWidget
from onegov.form.widgets import UploadWidget
from wtforms import FileField
from wtforms import SelectMultipleField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import widgets
from wtforms.validators import DataRequired, InputRequired


class MultiCheckboxField(SelectMultipleField):

    widget = MultiCheckboxWidget()
    contains_labels = True

    def __init__(self, *args, **kwargs):
        kwargs['option_widget'] = widgets.CheckboxInput()
        super().__init__(*args, **kwargs)


class OrderedMultiCheckboxField(MultiCheckboxField):
    widget = OrderedMultiCheckboxWidget()


class UploadField(FileField):
    """ A custom file field that turns the uploaded file into a compressed
    base64 string together with the filename, size and mimetype.

    """

    widget = UploadWidget()

    @property
    def data(self):
        caller = inspect.currentframe().f_back.f_locals.get('self')

        # give the required validators the idea that the data is there
        # when the action was to keep the current file - an evil approach
        if isinstance(caller, (DataRequired, InputRequired)):
            truthy = (
                getattr(self, '_data', None) or
                getattr(self, 'action', None) == 'keep'
            )

            return truthy

        return getattr(self, '_data', None)

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def is_image(self):
        return self.data and\
            self.data.get('mimetype') in IMAGE_MIME_TYPES_AND_SVG

    def process_formdata(self, valuelist):
        # the upload widget optionally includes an action with the request,
        # indicating if the existing file should be replaced, kept or deleted
        if valuelist:
            if len(valuelist) == 2:
                self.action, fieldstorage = valuelist
            else:
                self.action = 'replace'
                fieldstorage = valuelist[0]

            if self.action == 'replace':
                self.data = self.process_fieldstorage(fieldstorage)
            elif self.action == 'delete':
                self.data = {}
            elif self.action == 'keep':
                pass
            else:
                raise NotImplementedError()
        else:
            self.data = {}

    def process_fieldstorage(self, fs):
        self.file = getattr(fs, 'file', getattr(fs, 'stream', None))
        self.filename = getattr(fs, 'filename', None)

        if not self.file:
            return {}

        self.file.seek(0)

        try:
            return binary_to_dictionary(self.file.read(), self.filename)
        finally:
            self.file.seek(0)


class UploadFileWithORMSupport(UploadField):
    """ Extends the upload field with onegov.file support. """

    def __init__(self, *args, **kwargs):
        self.file_class = kwargs.pop('file_class')
        super().__init__(*args, **kwargs)

    def populate_obj(self, obj, name):
        if not getattr(self, 'action', None):
            return

        if self.action == 'keep':
            pass

        elif self.action == 'delete':
            setattr(obj, name, None)

        elif self.action == 'replace':
            if self.file:
                self.file.filename = self.filename
                self.file.seek(0)

                setattr(obj, name, self.file_class(
                    name=self.filename,
                    reference=as_fileintent(self.file, self.filename)
                ))
        else:
            raise NotImplementedError(f"Unknown action: {self.action}")

    def process_data(self, value):
        if value:
            self.data = {
                'filename': value.name,
                'size': value.reference.file.content_length,
                'mimetype': value.reference.content_type
            }
        else:
            super().process_data(value)


class HtmlField(TextAreaField):
    """ A textfield with html with integrated sanitation. """

    def __init__(self, *args, **kwargs):
        self.form = kwargs.get('_form')

        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['class_'] = 'editor'

        super().__init__(*args, **kwargs)

    def pre_validate(self, form):
        self.data = sanitize_html(self.data)


class TagsField(StringField):
    """ A tags field for use in conjunction with this library:

    https://github.com/developit/tags-input

    """

    widget = TagsWidget()

    def process_formdata(self, valuelist):
        if valuelist:
            values = (v.strip() for v in valuelist[0].split(','))
            values = (v for v in values if v)

            self.data = list(values)
        else:
            self.data = []

    def process_data(self, value):
        self.data = value and ','.join(value) or ''


class IconField(StringField):
    """ Selects an icon out of a number of icons. """

    widget = IconWidget()


class PhoneNumberField(StringField):
    """ A string field with support for phone numbers. """

    def __init__(self, *args, **kwargs):
        validators = kwargs.pop('validators', [])
        self.country = kwargs.pop('country', 'CH')
        if not any([isinstance(v, ValidPhoneNumber) for v in validators]):
            validators.append(ValidPhoneNumber(self.country))
        kwargs['validators'] = validators

        super().__init__(*args, **kwargs)

    @property
    def formatted_data(self):
        try:
            return phonenumbers.format_number(
                phonenumbers.parse(self.data, self.country),
                phonenumbers.PhoneNumberFormat.E164
            )
        except Exception:
            return self.data
