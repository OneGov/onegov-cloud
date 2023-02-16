import inspect
import phonenumbers
import sedate

from cssutils.css import CSSStyleSheet
from itertools import zip_longest
from onegov.core.html import sanitize_html
from onegov.core.utils import binary_to_dictionary
from onegov.core.utils import dictionary_to_binary
from onegov.file.utils import as_fileintent
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form import log
from onegov.form.utils import path_to_filename
from onegov.form.validators import ValidPhoneNumber
from onegov.form.widgets import ChosenSelectWidget
from onegov.form.widgets import HoneyPotWidget
from onegov.form.widgets import IconWidget
from onegov.form.widgets import MultiCheckboxWidget
from onegov.form.widgets import OrderedMultiCheckboxWidget
from onegov.form.widgets import PanelWidget
from onegov.form.widgets import PreviewWidget
from onegov.form.widgets import TagsWidget
from onegov.form.widgets import TextAreaWithTextModules
from onegov.form.widgets import UploadWidget
from onegov.form.widgets import UploadMultipleWidget
from werkzeug.datastructures import MultiDict
from wtforms_components import TimeField as DefaultTimeField
from wtforms.fields import DateTimeLocalField as DateTimeLocalFieldBase
from wtforms.fields import Field
from wtforms.fields import FieldList
from wtforms.fields import FileField
from wtforms.fields import SelectField
from wtforms.fields import SelectMultipleField
from wtforms.fields import StringField
from wtforms.fields import TelField
from wtforms.fields import TextAreaField
from wtforms.utils import unset_value
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError
from wtforms.widgets import CheckboxInput

FIELDS_NO_RENDERED_PLACEHOLDER = (
    'MultiCheckboxField', 'RadioField', 'OrderedMultiCheckboxField',
    'UploadField', 'ChosenSelectField', 'ChosenSelectMultipleField',
    'PreviewField', 'PanelField', 'UploadFileWithORMSupport'
)


class TimeField(DefaultTimeField):
    """
    Fixes the case for MS Edge Browser that returns the 'valuelist'
    as [08:00:000] instead of [08:00]. This is only the case of the time
    is set with the js popup, not when switching the time
    e.g. with the arrow keys on the form.
    """

    def process_formdata(self, valuelist):
        valuelist = [t[:5] for t in valuelist]
        return super().process_formdata(valuelist)


class MultiCheckboxField(SelectMultipleField):

    widget = MultiCheckboxWidget()
    contains_labels = True

    def __init__(self, *args, **kwargs):
        kwargs['option_widget'] = CheckboxInput()
        super().__init__(*args, **kwargs)

    def __iter__(self):
        for opt in super().__iter__():
            if self.render_kw and 'disabled' in self.render_kw:
                opt.render_kw = opt.render_kw or {}
                opt.render_kw['disabled'] = self.render_kw['disabled']
            yield opt


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
                getattr(self, '_data', None)
                or getattr(self, 'action', None) == 'keep'
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

        if valuelist:
            if len(valuelist) == 4:
                # resend_upload
                self.action = valuelist[0]
                fieldstorage = valuelist[1]
                self.data = binary_to_dictionary(
                    dictionary_to_binary({'data': valuelist[3]}),
                    valuelist[2]
                )
            elif len(valuelist) == 2:
                # force_simple
                self.action, fieldstorage = valuelist
            else:
                # default
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
        self.filename = path_to_filename(getattr(fs, 'filename', None))

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

    def create(self):
        if not getattr(self, 'file', None):
            return None

        self.file.filename = self.filename
        self.file.seek(0)

        return self.file_class(
            name=self.filename,
            reference=as_fileintent(self.file, self.filename)
        )

    def populate_obj(self, obj, name):
        if not getattr(self, 'action', None):
            return

        if self.action == 'keep':
            pass

        elif self.action == 'delete':
            setattr(obj, name, None)

        elif self.action == 'replace':
            setattr(obj, name, self.create())

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


class UploadMultipleField(FieldList, FileField):
    """ A custom file field that turns the uploaded files into a list of
    compressed base64 strings together with the filename, size and mimetype.

    This acts both like a single file field with multiple and like a list
    of :class:`onegov.form.fields.UploadFile` for uploaded files. This way
    we get the best of both worlds.

    """

    widget = UploadMultipleWidget()

    upload_field_class = UploadField
    upload_widget = UploadWidget()

    def __init__(
        self,
        label=None,
        validators=None,
        filters=(),
        description='',
        id=None,
        default=(),
        widget=None,
        render_kw=None,
        name=None,
        upload_widget=None,
        _form=None,
        _prefix='',
        _translations=None,
        _meta=None,
    ):
        if upload_widget is None:
            upload_widget = self.upload_widget

        # a lot of the arguments we just pass through to the subfield
        unbound_field = self.upload_field_class(
            validators=validators,
            filters=filters,
            description=description,
            widget=upload_widget,
            render_kw=render_kw,
        )
        super().__init__(
            unbound_field,
            label,
            min_entries=0,
            max_entries=None,
            id=id,
            default=default,
            widget=widget,
            render_kw=render_kw,
            name=name,
            _form=_form,
            _prefix=_prefix,
            _translations=_translations,
            _meta=_meta
        )

    def process(self, formdata, data=unset_value, extra_filters=None):
        self.process_errors = []

        # process the sub-fields
        super().process(formdata, data=data, extra_filters=extra_filters)

        # process the top-level multiple file field
        if formdata is not None:
            if self.name in formdata:
                self.raw_data = formdata.getlist(self.name)
            else:
                self.raw_data = []

            try:
                self.process_formdata(self.raw_data)
            except ValueError as e:
                self.process_errors.append(e.args[0])

    def process_formdata(self, valuelist):
        if not valuelist:
            return

        for fs in valuelist:
            if not (hasattr(fs, 'file') or hasattr(fs, 'stream')):
                # don't create an entry if we didn't get a fieldstorage
                continue

            # we fake the formdata for the new field
            # we use a werkzeug MultiDict because the webob version
            # needs to get wrapped to be usable in WTForms
            formdata = MultiDict()
            name = f'{self.short_name}{self._separator}{len(self)}'
            formdata.add(name, fs)
            self._add_entry(formdata)


class UploadMultipleFilesWithORMSupport(UploadMultipleField):
    """ Extends the upload multiple field with onegov.file support. """

    upload_field_class = UploadFileWithORMSupport

    def __init__(self, *args, **kwargs):
        self.file_class = kwargs.pop('file_class')
        super().__init__(*args, **kwargs)

    def populate_obj(self, obj, name):
        files = getattr(obj, name, None)
        output = []
        for field, file in zip_longest(self.entries, files):
            dummy = object()
            dummy.file = file
            field.populate_obj(dummy, 'file')
            if dummy.file is not None:
                output.append(dummy.file)

        setattr(obj, name, output)


class TextAreaFieldWithTextModules(TextAreaField):
    """ A textfield with text module selection/insertion. """

    widget = TextAreaWithTextModules()


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


class CssField(TextAreaField):
    """ A textfield with css validation. """

    def post_validate(self, form, validation_stopped):
        if self.data:
            try:
                CSSStyleSheet().cssText = self.data
            except Exception as e:
                raise ValidationError(str(e))


class TagsField(StringField):
    """ A tags field for use in conjunction with this library:

    https://github.com/developit/tags-input

    """

    widget = TagsWidget()

    def process_formdata(self, valuelist):
        if valuelist == ['[]']:
            self.data = []
        elif valuelist:
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


class PhoneNumberField(TelField):
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


class ChosenSelectField(SelectField):
    """ A select field with chosen.js support. """

    widget = ChosenSelectWidget()


class ChosenSelectMultipleField(SelectMultipleField):
    """ A multiple select field with chosen.js support. """

    widget = ChosenSelectWidget(multiple=True)


class PreviewField(Field):

    widget = PreviewWidget()

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields', ())
        self.url = kwargs.pop('url', None)
        self.events = kwargs.pop('events', ())
        self.display = kwargs.pop('display', 'inline')

        super().__init__(*args, **kwargs)

    def populate_obj(self, obj, name):
        pass


class PanelField(Field):
    """ Shows a panel as part of the form (no input, no lael). """

    widget = PanelWidget()

    def __init__(self, *args, **kwargs):
        self.text = kwargs.pop('text')
        self.kind = kwargs.pop('kind')
        self.hide_label = kwargs.pop('hide_label', True)
        super().__init__(*args, **kwargs)

    def populate_obj(self, obj, name):
        pass


class DateTimeLocalField(DateTimeLocalFieldBase):
    """ A custom implementation of the DateTimeLocalField to fix issues with
    the format and the datetimepicker plugin.

    """

    def __init__(self, **kwargs):
        kwargs['format'] = '%Y-%m-%dT%H:%M'
        super(DateTimeLocalField, self).__init__(**kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            valuelist = [' '.join(valuelist).replace(' ', 'T')]
            if len(valuelist[0]) != 16:
                valuelist[0] = valuelist[0][0:16]
        super(DateTimeLocalField, self).process_formdata(valuelist)


class TimezoneDateTimeField(DateTimeLocalField):
    """ A datetime field data returns the date with the given timezone
    and expects dateime values with a timezone.

    Used together with :class:`onegov.core.orm.types.UTCDateTime`.

    """

    def __init__(self, *args, **kwargs):
        self.timezone = kwargs.pop('timezone')
        super().__init__(*args, **kwargs)

    def process_data(self, value):
        if value:
            value = sedate.to_timezone(value, self.timezone)
            value.replace(tzinfo=None)

        super().process_data(value)

    def process_formdata(self, valuelist):
        super().process_formdata(valuelist)

        if self.data:
            self.data = sedate.replace_timezone(self.data, self.timezone)


class HoneyPotField(StringField):
    """ A field to identify bots.

    A honey pot field is hidden using CSS and therefore not visible for users
    but bots (probably). We therefore expect this field to be empty at any
    time and throw an error if provided as well as adding a log message to
    optionally ban the IP.

    To add honey pot fields to your (public) forms, give it a reasonable name,
    but not one that might be autofilled by browsers, e.g.:

        delay = HoneyPotField()

    """

    widget = HoneyPotWidget()

    def __init__(self, *args, **kwargs):
        kwargs['label'] = ''
        kwargs['validators'] = ''
        kwargs['description'] = ''
        kwargs['default'] = ''
        super().__init__(*args, **kwargs)
        self.type = 'LazyWolvesField'

    def post_validate(self, form, validation_stopped):
        if self.data:
            log.info(f'Honeypot used by {form.request.client_addr}')
            raise ValidationError('Invalid value')
