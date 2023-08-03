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


from typing import Any, IO, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from datetime import datetime
    from depot.fields.upload import UploadedFile
    from onegov.core.types import EmptyDict, FileDict
    from onegov.file import File
    from onegov.form.types import Filter, RawFormValue, Validator, Widget
    from wtforms import Form as BaseForm


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

    def process_formdata(self, valuelist: list['RawFormValue']) -> None:
        if not valuelist:
            return

        valuelist = [t[:5] for t in valuelist]  # type:ignore[index]
        super().process_formdata(valuelist)


class MultiCheckboxField(SelectMultipleField):
    widget = MultiCheckboxWidget()
    option_widget = CheckboxInput()
    contains_labels = True


class OrderedMultiCheckboxField(MultiCheckboxField):
    widget = OrderedMultiCheckboxWidget()


class UploadField(FileField):
    """ A custom file field that turns the uploaded file into a compressed
    base64 string together with the filename, size and mimetype.

    """

    widget = UploadWidget()
    action: Literal['keep', 'replace', 'delete']
    file: IO[bytes] | None
    filename: str | None

    @property
    def data(self) -> 'FileDict | EmptyDict | None':
        frame = inspect.currentframe()
        assert frame is not None and frame.f_back is not None
        caller = frame.f_back.f_locals.get('self')

        # give the required validators the idea that the data is there
        # when the action was to keep the current file - an evil approach
        if isinstance(caller, (DataRequired, InputRequired)):
            truthy = (
                getattr(self, '_data', None)
                or getattr(self, 'action', None) == 'keep'
            )

            return truthy  # type:ignore[return-value]

        return getattr(self, '_data', None)

    @data.setter
    def data(self, value: 'FileDict | EmptyDict') -> None:
        self._data = value

    @property
    def is_image(self) -> bool:
        return (self.data or {}).get('mimetype') in IMAGE_MIME_TYPES_AND_SVG

    def process_formdata(self, valuelist: list['RawFormValue']) -> None:

        if not valuelist:
            self.data = {}
            return

        fieldstorage: 'RawFormValue'
        action: 'RawFormValue'
        if len(valuelist) == 4:
            # resend_upload
            action = valuelist[0]
            fieldstorage = valuelist[1]
            self.data = binary_to_dictionary(
                dictionary_to_binary({'data': str(valuelist[3])}),
                str(valuelist[2])
            )
        elif len(valuelist) == 2:
            # force_simple
            action, fieldstorage = valuelist
        else:
            # default
            action = 'replace'
            fieldstorage = valuelist[0]

        if action == 'replace':
            self.action = 'replace'
            self.data = self.process_fieldstorage(fieldstorage)
        elif action == 'delete':
            self.action = 'delete'
            self.data = {}
        elif action == 'keep':
            self.action = 'keep'
        else:
            raise NotImplementedError()

    def process_fieldstorage(
        self,
        fs: 'RawFormValue'
    ) -> 'FileDict | EmptyDict':

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

    file_class: type['File']

    def __init__(self, *args: Any, **kwargs: Any):
        self.file_class = kwargs.pop('file_class')
        super().__init__(*args, **kwargs)

    def create(self) -> 'File | None':
        if not getattr(self, 'file', None):
            return None

        assert self.file is not None
        self.file.filename = self.filename  # type:ignore[attr-defined]
        self.file.seek(0)

        return self.file_class(  # type:ignore[misc]
            name=self.filename,
            reference=as_fileintent(self.file, self.filename)
        )

    def populate_obj(self, obj: object, name: str) -> None:
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

    def process_data(self, value: 'UploadedFile | None') -> None:
        if value:
            self.data = {  # type:ignore[assignment]
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
        label: str | None = None,
        validators: 'Sequence[Validator] | None' = None,
        filters: 'Sequence[Filter]' = (),
        description: str = '',
        id: str | None = None,
        default: 'Sequence[FileDict]' = (),
        widget: 'Widget | None' = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        upload_widget: 'Widget | None' = None,
        _form: 'BaseForm | None' = None,
        _prefix: str = '',
        _translations: object = None,
        _meta: object = None,
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

    def __bool__(self) -> Literal[True]:
        # because FieldList implements __len__ this field would evaluate
        # to False if no files have been uploaded, which is not generally
        # what we want
        return True

    def process(
        self,
        formdata: 'MultiDict[str, RawFormValue]',
        data: object = unset_value,
        extra_filters: 'Sequence[Filter] | None' = None
    ) -> None:
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

    def process_formdata(self, valuelist: list['RawFormValue']) -> None:
        if not valuelist:
            return

        for fs in valuelist:
            if not (hasattr(fs, 'file') or hasattr(fs, 'stream')):
                # don't create an entry if we didn't get a fieldstorage
                continue

            # we fake the formdata for the new field
            # we use a werkzeug MultiDict because the webob version
            # needs to get wrapped to be usable in WTForms
            formdata: 'MultiDict[str, RawFormValue]' = MultiDict()
            name = f'{self.short_name}{self._separator}{len(self)}'
            formdata.add(name, fs)
            self._add_entry(formdata)


class _DummyFile:
    file: 'File | None'


class UploadMultipleFilesWithORMSupport(UploadMultipleField):
    """ Extends the upload multiple field with onegov.file support. """

    file_class: type['File']
    upload_field_class = UploadFileWithORMSupport

    def __init__(self, *args: Any, **kwargs: Any):
        self.file_class = kwargs.pop('file_class')
        super().__init__(*args, **kwargs)

    def populate_obj(self, obj: object, name: str) -> None:
        files = getattr(obj, name, ())
        output: list['File'] = []
        for field, file in zip_longest(self.entries, files):
            dummy = _DummyFile()
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

    data: str

    def __init__(self, *args: Any, **kwargs: Any):
        self.form = kwargs.get('_form')

        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['class_'] = 'editor'

        super().__init__(*args, **kwargs)

    def pre_validate(self, form: 'BaseForm') -> None:
        self.data = sanitize_html(self.data)


class CssField(TextAreaField):
    """ A textfield with css validation. """

    def post_validate(
        self,
        form: 'BaseForm',
        validation_stopped: bool
    ) -> None:
        if self.data:
            try:
                CSSStyleSheet().cssText = self.data
            except Exception as exception:
                raise ValidationError(str(exception)) from exception


class TagsField(StringField):
    """ A tags field for use in conjunction with this library:

    https://github.com/developit/tags-input

    """

    widget = TagsWidget()
    # FIXME: Why does data have a different shape depending on if it's
    #        passed in by the form or the object?! This seems like a bug
    data: str | list[str]

    def process_formdata(self, valuelist: list['RawFormValue']) -> None:
        if not valuelist:
            self.data = []
            return

        values_str = valuelist[0]
        if isinstance(values_str, str) and values_str != '[]':
            # FIXME: Shouldn't this strip [] from the ends?
            values = (v.strip() for v in values_str.split(','))
            self.data = [v for v in values if v]
        else:
            self.data = []

    def process_data(self, value: list[str] | None) -> None:
        self.data = ','.join(value) if value else ''


class IconField(StringField):
    """ Selects an icon out of a number of icons. """

    widget = IconWidget()


class PhoneNumberField(TelField):
    """ A string field with support for phone numbers. """

    validators: 'Sequence[Validator]'

    def __init__(self, *args: Any, country: str = 'CH', **kwargs: Any):

        self.country = country
        super().__init__(*args, **kwargs)

        # ensure the ValidPhoneNumber validator gets added
        if not any(isinstance(v, ValidPhoneNumber) for v in self.validators):
            # validators can be any sequence type, so it might not be mutable
            # so we have to first convert to a list if that's the case
            if not isinstance(self.validators, list):
                self.validators = list(self.validators)
            self.validators.append(ValidPhoneNumber(self.country))

    @property
    def formatted_data(self) -> str:
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

    fields: 'Sequence[str]'
    events: 'Sequence[str]'
    url: 'Callable[[Any], str] | str | None'
    display: str

    widget = PreviewWidget()

    def __init__(
        self,
        *args: Any,
        fields: 'Sequence[str]' = (),
        url: 'Callable[[Any], str] | str | None' = None,
        events: 'Sequence[str]' = (),
        display: str = 'inline',
        **kwargs: Any
    ):
        self.fields = fields
        self.url = url
        self.events = events
        self.display = display

        super().__init__(*args, **kwargs)

    def populate_obj(self, obj: object, name: str) -> None:
        pass


class PanelField(Field):
    """ Shows a panel as part of the form (no input, no label). """

    widget = PanelWidget()

    def __init__(
        self,
        *args: Any,
        text: str,
        kind: str,
        hide_label: bool = True,
        **kwargs: Any
    ):
        self.text = text
        self.kind = kind
        self.hide_label = hide_label
        super().__init__(*args, **kwargs)

    def populate_obj(self, obj: object, name: str) -> None:
        pass


class DateTimeLocalField(DateTimeLocalFieldBase):
    """ A custom implementation of the DateTimeLocalField to fix issues with
    the format and the datetimepicker plugin.

    """

    def __init__(
        self,
        label: str | None = None,
        validators: 'Sequence[Validator] | None' = None,
        format: str = '%Y-%m-%dT%H:%M',
        **kwargs: Any
    ):
        super(DateTimeLocalField, self).__init__(
            label=label,
            validators=validators,
            format=format,
            **kwargs
        )

    def process_formdata(self, valuelist: list['RawFormValue']) -> None:
        if valuelist:
            date_str = 'T'.join(valuelist).replace(' ', 'T')  # type:ignore
            valuelist = [date_str[:16]]
        super(DateTimeLocalField, self).process_formdata(valuelist)


class TimezoneDateTimeField(DateTimeLocalField):
    """ A datetime field data returns the date with the given timezone
    and expects dateime values with a timezone.

    Used together with :class:`onegov.core.orm.types.UTCDateTime`.

    """

    data: 'datetime | None'

    def __init__(self, *args: Any, timezone: str, **kwargs: Any):
        self.timezone = timezone
        super().__init__(*args, **kwargs)

    def process_data(self, value: 'datetime | None') -> None:
        if value:
            value = sedate.to_timezone(value, self.timezone)
            value.replace(tzinfo=None)

        super().process_data(value)

    def process_formdata(self, valuelist: list['RawFormValue']) -> None:
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

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs['label'] = ''
        kwargs['validators'] = ''
        kwargs['description'] = ''
        kwargs['default'] = ''
        super().__init__(*args, **kwargs)
        self.type = 'LazyWolvesField'

    def post_validate(
        self,
        form: 'BaseForm',
        validation_stopped: bool
    ) -> None:
        if self.data:
            log.info(f'Honeypot used by {form.request.client_addr}')
            raise ValidationError('Invalid value')
