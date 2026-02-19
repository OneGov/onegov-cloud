from __future__ import annotations

import inspect
import phonenumbers
import sedate

from cssutils.css import CSSStyleSheet  # type:ignore[import-untyped]
from datetime import timedelta
from enum import Enum
from itertools import zip_longest
from email_validator import validate_email, EmailNotValidError
from markupsafe import escape, Markup
from onegov.core.custom import json
from onegov.core.html import sanitize_html
from onegov.core.utils import binary_to_dictionary
from onegov.core.utils import dictionary_to_binary
from onegov.file.utils import as_fileintent
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form import log, _
from onegov.form.utils import path_to_filename
from onegov.form.validators import ValidPhoneNumber, WhitelistedMimeType
from onegov.form.widgets import ChosenSelectWidget
from onegov.form.widgets import LinkPanelWidget
from onegov.form.widgets import DurationInput
from onegov.form.widgets import HoneyPotWidget
from onegov.form.widgets import IconWidget
from onegov.form.widgets import MultiCheckboxWidget
from onegov.form.widgets import OrderedMultiCheckboxWidget
from onegov.form.widgets import PanelWidget
from onegov.form.widgets import PreviewWidget
from onegov.form.widgets import TagsWidget
from onegov.form.widgets import TextAreaWithTextModules
from onegov.form.widgets import TreeSelectWidget
from onegov.form.widgets import TypeAheadInput
from onegov.form.widgets import UploadWidget
from onegov.form.widgets import UploadMultipleWidget
from operator import itemgetter
from webcolors import name_to_hex, normalize_hex
from werkzeug.datastructures import MultiDict
from wtforms.fields import DateTimeLocalField as DateTimeLocalFieldBase
from wtforms.fields import Field
from wtforms.fields import FieldList
from wtforms.fields import FileField
from wtforms.fields import SelectField
from wtforms.fields import SelectMultipleField
from wtforms.fields import StringField
from wtforms.fields import TelField
from wtforms.fields import TextAreaField
from wtforms.fields import TimeField as DefaultTimeField
from wtforms.utils import unset_value
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import URL
from wtforms.validators import ValidationError
from wtforms.widgets import CheckboxInput, ColorInput, TextInput


from typing import Any, IO, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from collections.abc import Collection
    from datetime import datetime
    from onegov.core.types import FileDict as StrictFileDict
    from onegov.file import File
    from onegov.form import Form
    from onegov.form.types import (
        FormT, Filter, PricingRules, RawFormValue, Validators, Widget)
    from typing import NotRequired, TypedDict, Self
    from webob.request import _FieldStorageWithFile
    from wtforms.fields.choices import _Choice
    from wtforms.form import BaseForm
    from wtforms.meta import (
        _MultiDictLikeWithGetlist, _SupportsGettextAndNgettext, DefaultMeta)

    class FileDict(TypedDict, total=False):
        data: str
        filename: str | None
        mimetype: str
        size: int

    class TreeSelectNode(TypedDict):
        name: str
        value: str
        children: Sequence[TreeSelectNode]
        disabled: NotRequired[bool]
        isGroupSelectable: NotRequired[bool]
        htmlAttr: NotRequired[dict[str, str]]

    # this is only generic at type checking time
    class UploadMultipleBase(FieldList['UploadField']):
        pass

    _TreeSelectMixinBase = SelectField
else:
    UploadMultipleBase = FieldList
    _TreeSelectMixinBase = object


FIELDS_NO_RENDERED_PLACEHOLDER = (
    'MultiCheckboxField', 'RadioField', 'OrderedMultiCheckboxField',
    'UploadField', 'ChosenSelectField', 'ChosenSelectMultipleField',
    'PreviewField', 'PanelField', 'UploadFileWithORMSupport',
    'TreeSelectField', 'TreeSelectMultipleField'
)


class URLField(StringField):
    """
    A non-native version of the URL field that uses a default text field.

    It instead relies on `wtforms.validators.URL` and normalizes URLs with
    missing scheme to use `https://` or a given scheme by default. This
    behavior can be turned off by setting `default_scheme` to `None`.
    """
    def __init__(
        self,
        label: str | None = None,
        validators: Validators[FormT, Self] | None = None,
        filters: Sequence[Filter] = (),
        description: str = '',
        id: str | None = None,
        default: str | None = None,
        widget: Widget[Self] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        default_scheme: str | None = 'https',
        _form: BaseForm | None = None,
        _prefix: str = '',
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        *,
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
    ) -> None:

        if validators is None:
            validators = ()

        if not any(isinstance(validator, URL) for validator in validators):
            validators = [
                *validators,
                URL(allow_ip=False)
            ]

        self.default_scheme = default_scheme

        if default_scheme:
            if render_kw is None:
                render_kw = {}

            render_kw.setdefault('placeholder', f'{self.default_scheme}://')

        super().__init__(
            label=label,
            validators=validators,
            filters=filters,
            description=description,
            id=id,
            default=default,
            widget=widget,
            render_kw=render_kw,
            name=name,
            _form=_form,
            _prefix=_prefix,
            _translations=_translations,
            _meta=_meta,
        )

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if not valuelist:
            return

        # if no scheme was given, use the default scheme
        value = valuelist[0]
        if value and self.default_scheme and '://' not in value:
            valuelist[0] = f'{self.default_scheme}://{value}'

        super().process_formdata(valuelist)


class TimeField(DefaultTimeField):
    """
    Fixes the case for MS Edge Browser that returns the 'valuelist'
    as [08:00:000] instead of [08:00:00]. This is only the case of the time
    is set with the js popup, not when switching the time
    e.g. with the arrow keys on the form.
    """

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if not valuelist:
            return

        valuelist = [t[:8] for t in valuelist]  # type:ignore[index]
        super().process_formdata(valuelist)


# NOTE: For now this is exactly what we use it for: a 5 minute-granularity
#       input field with an hour and minute component. We can make this
#       more flexible in the future, if we need it.
class DurationField(Field):

    widget = DurationInput()

    data: timedelta | None

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if not (len(valuelist) == 2 and valuelist[0] and valuelist[1]):
            self.data = None
            return

        hours, minutes = map(int, valuelist)  # type: ignore[arg-type]
        if not (0 <= hours <= 24):
            self.data = None
            raise ValueError(_('Invalid number of hours'))
        if not (0 <= minutes <= 60) or (minutes % 5 != 0):
            self.data = None
            raise ValueError(_('Invalid number of minutes'))

        if not (hours or minutes):
            self.data = None
            return

        self.data = timedelta(hours=hours, minutes=minutes)


class TranslatedSelectField(SelectField):
    """ A select field which translates the option labels. """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ):
        self.choices_sorted = kwargs.pop('choices_sorted', False)
        super().__init__(*args, **kwargs)

    def iter_choices(self) -> Iterator[tuple[Any, str, bool, dict[str, Any]]]:
        choices = []

        for choice in super().iter_choices():
            result = list(choice)
            result[1] = self.meta.request.translate(result[1])

            if self.choices_sorted:
                choices.append(tuple(result))
            else:
                yield tuple(result)

        if self.choices_sorted:
            choices.sort(key=itemgetter(1))
            for choice in choices:
                yield choice


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

    def __init__(
        self,
        label: str | None = None,
        validators: Validators[FormT, Self] | None = None,
        filters: Sequence[Filter] = (),
        description: str = '',
        id: str | None = None,
        default: StrictFileDict | None = None,
        widget: Widget[Self] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        allowed_mimetypes: Collection[str] | None = None,
        _form: BaseForm | None = None,
        _prefix: str = '',
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        *,
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
    ):
        if validators:
            assert not any(isinstance(v, WhitelistedMimeType)
                           for v in validators), (
                'Use parameter "allowed_mimetypes" instead of adding a '
                'WhitelistedMimeType validator directly'
            )
        if allowed_mimetypes:
            self.mimetypes = set(allowed_mimetypes)
        else:
            self.mimetypes = set(WhitelistedMimeType.whitelist)

        super().__init__(
            label=label,
            validators=validators,
            filters=filters,
            description=description,
            id=id,
            default=default,
            widget=widget,
            render_kw=render_kw,
            name=name,
            _form=_form,
            _prefix=_prefix,
            _translations=_translations,
            _meta=_meta,
        )

    # this is not quite accurate, since it is either a dictionary with all
    # the keys or none of the keys, which would make type narrowing easier
    # unfortunately a union of two TypedDict will narrow to the TypedDict
    # with the fewest shared keys, which would always be an empty dictionary
    @property
    def data(self) -> StrictFileDict | FileDict | None:
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
    def data(self, value: FileDict) -> None:
        self._data = value

    @property
    def is_image(self) -> bool:
        if not self.data:
            return False
        return self.data.get('mimetype') in IMAGE_MIME_TYPES_AND_SVG

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:

        if not valuelist:
            self.data = {}
            return

        fieldstorage: RawFormValue
        action: RawFormValue
        if len(valuelist) == 4:
            # resend_upload
            action = valuelist[0]
            fieldstorage = valuelist[1]
            # NOTE: I'm not sure why mypy complains here, a total version
            #       of a TypedDict should be assignable to a non-total version
            self.data = binary_to_dictionary(  # type: ignore[assignment]
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
        fs: RawFormValue
    ) -> FileDict:

        self.file = getattr(fs, 'file', getattr(fs, 'stream', None))
        self.filename = path_to_filename(getattr(fs, 'filename', None))

        if not self.file:
            return {}

        self.file.seek(0)

        try:
            return binary_to_dictionary(self.file.read(), self.filename)  # type: ignore[return-value]
        finally:
            self.file.seek(0)

    def post_validate(
        self,
        form: BaseForm,
        validation_stopped: bool
    ) -> None:
        if self.data and self.mimetypes:
            if self.data.get('mimetype') not in self.mimetypes:
                raise ValidationError(_(
                    'Files of this type are not supported.'))


class UploadFileWithORMSupport(UploadField):
    """ Extends the upload field with onegov.file support. """

    file_class: type[File]

    def __init__(self, *args: Any, **kwargs: Any):
        self.file_class = kwargs.pop('file_class')
        super().__init__(*args, **kwargs)

    def create(self) -> File | None:
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
            raise NotImplementedError(f'Unknown action: {self.action}')

    def process_data(self, value: File | None) -> None:
        if value:
            try:
                size = value.reference.file.content_length
            except OSError:
                # if the file doesn't exist on disk we try to fail
                # silently for now
                size = -1
            self.data = {
                'filename': value.name,
                'size': size,
                'mimetype': value.reference.content_type
            }
        else:
            super().process_data(value)


class UploadMultipleField(UploadMultipleBase, FileField):
    """ A custom file field that turns the uploaded files into a list of
    compressed base64 strings together with the filename, size and mimetype.

    This acts both like a single file field with multiple and like a list
    of :class:`onegov.form.fields.UploadFile` for uploaded files. This way
    we get the best of both worlds.

    """

    widget = UploadMultipleWidget()
    raw_data: list[RawFormValue]

    if TYPE_CHECKING:
        _separator: str

        def _add_entry(self, d: _MultiDictLikeWithGetlist, /) -> UploadField:
            ...

    upload_field_class: type[UploadField] = UploadField
    upload_widget: Widget[UploadField] = UploadWidget()

    def __init__(
        self,
        label: str | None = None,
        validators: Validators[FormT, UploadField] | None = None,
        filters: Sequence[Filter] = (),
        description: str = '',
        id: str | None = None,
        default: Sequence[FileDict] = (),
        widget: Widget[Self] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        upload_widget: Widget[UploadField] | None = None,
        allowed_mimetypes: Collection[str] | None = None,
        _form: BaseForm | None = None,
        _prefix: str = '',
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        *,
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
        # if we change the upload_field_class there may be additional
        # parameters that are allowed so we pass them through
        **extra_arguments: Any
    ):
        if upload_widget is None:
            upload_widget = self.upload_widget

        if allowed_mimetypes:
            self.mimetypes = set(allowed_mimetypes)
        else:
            self.mimetypes = set(WhitelistedMimeType.whitelist)

        # a lot of the arguments we just pass through to the subfield
        unbound_field = self.upload_field_class(
            filters=filters,
            description=description,
            widget=upload_widget,
            render_kw=render_kw,
            allowed_mimetypes=allowed_mimetypes,
            validators=validators,  # type: ignore[arg-type]
            **extra_arguments
        )
        super().__init__(
            unbound_field,
            label,
            min_entries=0,
            max_entries=None,
            id=id,
            default=default,
            widget=widget,  # type:ignore[arg-type]
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
        formdata: _MultiDictLikeWithGetlist | None,
        data: object = unset_value,
        extra_filters: Sequence[Filter] | None = None
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

    def append_entry_from_field_storage(
        self,
        fs: _FieldStorageWithFile
    ) -> UploadField:
        # we fake the formdata for the new field
        # we use a werkzeug MultiDict because the WebOb version
        # needs to get wrapped to be usable in WTForms
        formdata: MultiDict[str, RawFormValue] = MultiDict()
        name = f'{self.short_name}{self._separator}{len(self)}'
        formdata.add(name, fs)
        return self._add_entry(formdata)

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if not valuelist:
            return

        # only create entries for valid field storage
        for value in valuelist:
            if isinstance(value, str):
                continue

            if hasattr(value, 'file') or hasattr(value, 'stream'):
                self.append_entry_from_field_storage(value)


class _DummyFile:
    file: File | None


class UploadMultipleFilesWithORMSupport(UploadMultipleField):
    """ Extends the upload multiple field with onegov.file support. """

    file_class: type[File]
    added_files: list[File]
    upload_field_class = UploadFileWithORMSupport

    def __init__(self, *args: Any, **kwargs: Any):
        self.file_class = kwargs['file_class']
        super().__init__(*args, **kwargs)

    def populate_obj(self, obj: object, name: str) -> None:
        self.added_files = []
        files = getattr(obj, name, ())
        output: list[File] = []
        for field, file in zip_longest(self.entries, files):
            if field is None:
                # this generally shouldn't happen, but we should
                # guard against it anyways, since it can happen
                # if people manually call pop_entry()
                break

            dummy = _DummyFile()
            dummy.file = file
            field.populate_obj(dummy, 'file')
            # avoid generating multiple links to the same file
            if dummy.file is not None and dummy.file not in output:
                output.append(dummy.file)
                if (
                    dummy.file is not file
                    # an upload field may mark a file as having already
                    # existed previously, in this case we don't consider
                    # it having being added
                    and getattr(field, 'existing_file', None) is None
                ):
                    # added file
                    self.added_files.append(dummy.file)

        setattr(obj, name, output)


class TextAreaFieldWithTextModules(TextAreaField):
    """ A textfield with text module selection/insertion. """

    widget = TextAreaWithTextModules()


class VideoURLField(URLField):

    pass


class HtmlField(TextAreaField):
    """ A textfield with html with integrated sanitation. """

    data: Markup | None

    def __init__(self, *args: Any, **kwargs: Any):
        self.form = kwargs.get('_form')

        if 'render_kw' not in kwargs or not kwargs['render_kw'].get('class_'):
            kwargs['render_kw'] = kwargs.get('render_kw', {})
            kwargs['render_kw']['class_'] = 'editor'

        super().__init__(*args, **kwargs)

    def pre_validate(self, form: BaseForm) -> None:
        self.data = sanitize_html(self.data)


class CssField(TextAreaField):
    """ A textfield with css validation. """

    def post_validate(
        self,
        form: BaseForm,
        validation_stopped: bool
    ) -> None:
        if self.data:
            try:
                CSSStyleSheet().cssText = self.data
            except Exception as exception:
                raise ValidationError(str(exception)) from exception


class MarkupField(TextAreaField):
    """
    A textfield with markup with no sanitation.

    This field is inherently unsafe and should be avoided, use with care!
    """

    data: Markup | None

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if valuelist:
            assert isinstance(valuelist[0], str)
            self.data = Markup(valuelist[0])  # nosec: B704
        else:
            self.data = None

    def process_data(self, value: str | None) -> None:
        # NOTE: For regular data we do the escape, just to ensure
        #       that we use this field consistenly and don't pass
        #       in raw strings
        self.data = escape(value) if value is not None else None


class TagsField(StringField):
    """ A tags field for use in conjunction with this library:

    https://github.com/developit/tags-input

    """

    widget = TagsWidget()
    # FIXME: Why does data have a different shape depending on if it's
    #        passed in by the form or the object?! This seems like a bug
    data: str | list[str]  # type:ignore[assignment]

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if not valuelist:
            self.data = []
            return

        values_str = valuelist[0]
        if isinstance(values_str, str) and values_str != '':
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
    def formatted_data(self) -> str | None:
        try:
            return phonenumbers.format_number(
                phonenumbers.parse(self.data or '', self.country),
                phonenumbers.PhoneNumberFormat.E164
            )
        except Exception:
            return self.data


class _TreeSelectMixin(_TreeSelectMixinBase):

    def __init__(
        self,
        label: str | None = None,
        validators: Validators[FormT, Self] | None = None,
        coerce: Callable[[Any], Any] = str,
        choices: Iterable[TreeSelectNode] | None = None,
        validate_choice: bool = True,
        *,
        filters: Sequence[Filter] = (),
        description: str = '',
        id: str | None = None,
        default: object | None = None,
        widget: Widget[Self] | None = None,
        option_widget: Widget[SelectField._Option] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        _form: BaseForm | None = None,
        _prefix: str = '',
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
        discount: dict[str, float] | None = None,
    ) -> None:

        if not render_kw:
            render_kw = {}

        if choices is None:
            choices = []
        elif not isinstance(choices, (list, tuple)):
            choices = list(choices)

        render_kw['data-choices'] = json.dumps(choices)

        super().__init__(
            label=label,
            validators=validators,
            coerce=coerce,
            choices=self.flatten_choices(choices) if choices else None,
            validate_choice=validate_choice,
            filters=filters,
            description=description,
            id=id,
            default=default,
            widget=widget,
            option_widget=option_widget,
            render_kw=render_kw,
            name=name,
            _form=_form,
            _prefix=_prefix,
            _translations=_translations,
            _meta=_meta,
        )

    def flatten_choices(
        self,
        choices: Iterable[TreeSelectNode]
    ) -> Iterator[_Choice]:
        for choice in choices:
            yield choice['value'], choice['name']
            yield from self.flatten_choices(choice['children'])

    def set_choices(self, choices: Iterable[TreeSelectNode]) -> None:
        if not self.render_kw:
            self.render_kw = {}

        self.render_kw['data-choices'] = json.dumps(choices)
        self.choices = list(self.flatten_choices(choices))


class TreeSelectField(_TreeSelectMixin, SelectField):
    """ A select field with treeselectjs support. """

    widget = TreeSelectWidget()


class TreeSelectMultipleField(_TreeSelectMixin, SelectMultipleField):
    """ A select field with treeselectjs support. """

    widget = TreeSelectWidget(multiple=True)


class ChosenSelectField(SelectField):
    """ A select field with chosen.js support. """

    widget = ChosenSelectWidget()


class ChosenSelectMultipleField(SelectMultipleField):
    """ A multiple select field with chosen.js support. """

    widget = ChosenSelectWidget(multiple=True)


class ChosenSelectMultipleEmailField(SelectMultipleField):

    widget = ChosenSelectWidget(multiple=True)

    def pre_validate(self, form: BaseForm) -> None:
        super().pre_validate(form)
        if not self.data:
            return
        for email in self.data:
            try:
                validate_email(email)
            except EmailNotValidError as e:
                raise ValidationError(_('Not a valid email')) from e


class PreviewField(Field):

    fields: Sequence[str]
    events: Sequence[str]
    url: Callable[[DefaultMeta], str | None] | str | None
    display: str

    widget = PreviewWidget()

    def __init__(
        self,
        *args: Any,
        fields: Sequence[str] = (),
        url: Callable[[DefaultMeta], str | None] | str | None = None,
        events: Sequence[str] = (),
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


class URLPanelField(PanelField):

    widget = LinkPanelWidget()


class DateTimeLocalField(DateTimeLocalFieldBase):
    """ A custom implementation of the DateTimeLocalField to fix issues with
    the format and the datetimepicker plugin.

    """

    def __init__(
        self,
        label: str | None = None,
        validators: Validators[FormT, Self] | None = None,
        format: str = '%Y-%m-%dT%H:%M',
        **kwargs: Any
    ):
        super().__init__(
            label=label,
            validators=validators,
            format=format,
            **kwargs
        )

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if valuelist:
            date_str = 'T'.join(valuelist).replace(' ', 'T')  # type:ignore
            valuelist = [date_str[:16]]
        super().process_formdata(valuelist)


class TimezoneDateTimeField(DateTimeLocalField):
    """ A datetime field data returns the date with the given timezone
    and expects dateime values with a timezone.

    Used together with :class:`onegov.core.orm.types.UTCDateTime`.

    """

    data: datetime | None

    def __init__(self, *args: Any, timezone: str, **kwargs: Any):
        self.timezone = timezone
        super().__init__(*args, **kwargs)

    def process_data(self, value: datetime | None) -> None:
        if value:
            value = sedate.to_timezone(value, self.timezone)
            # FIXME: This statement has no effect. replace() returns a new
            # datetime.
            value.replace(tzinfo=None)

        super().process_data(value)

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
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
        form: Form,  # type:ignore[override]
        validation_stopped: bool
    ) -> None:
        if self.data:
            log.info(f'Honeypot used by {form.request.client_addr}')
            raise ValidationError('Invalid value')


class ColorField(StringField):
    """ A string field that renders a html5 color picker and coerces
    to a normalized six digit hex string.

    It will result in a process_error for invalid colors.
    """

    widget = ColorInput()

    def coerce(self, value: object) -> str | None:
        if not isinstance(value, str) or value == '':
            return None

        try:
            if not value.startswith('#'):
                value = name_to_hex(value)
            return normalize_hex(value)
        except ValueError:
            msg = self.gettext(_('Not a valid color.'))
            raise ValueError(msg) from None

    def process_data(self, value: object) -> None:
        self.data = self.coerce(value)

    def process_formdata(self, valuelist: list[RawFormValue]) -> None:
        if not valuelist:
            self.data = None
            return

        self.data = self.coerce(valuelist[0])


class TypeAheadField(StringField):
    """ A string field with typeahead.

    Requires an url with the placeholder `%QUERY` for the search term.

    """

    url: Callable[[DefaultMeta], str | None] | str | None

    widget = TypeAheadInput()

    def __init__(
        self,
        *args: Any,
        url: Callable[[DefaultMeta], str | None] | str | None = None,
        **kwargs: Any
    ):
        self.url = url

        super().__init__(*args, **kwargs)


class MapboxPlaceDetail(Enum):
    """Determines the level of geographical precision of autofill. """

    # Line levels (specific parts of the street address)
    STREET_NUMBER = 'address-line1'  # Street number and name
    APPARTMENT_OR_FLOOR = 'address-line2'  # Apartment, suite, floor, etc.

    # Administrative levels (geographic areas)
    # Use this to match canton in CH:
    LEAST_SPECIFIC = 'address-level1'

    # Use this to match place municipality
    MORE_SPECIFIC = 'address-level2'

    # The most specific area, not commonly used.
    MOST_SPECIFIC = 'address-level3'


class PlaceAutocompleteField(StringField):
    """Provides address completion for places (via mapbox_address_autofill.js).
    """

    widget = TextInput()

    def __init__(self,
                 autocomplete_attribute: MapboxPlaceDetail | None = None,
                 *args: Any,
                 **kwargs: Any):

        form = kwargs.get('_form')
        if form is not None:
            form.meta.request.include('mapbox_address_autofill')
        if 'render_kw' not in kwargs:
            kwargs['render_kw'] = {}

        effective_autocomplete_attribute = (
            autocomplete_attribute or MapboxPlaceDetail.MORE_SPECIFIC
        )
        kwargs['render_kw']['autocomplete'] = (
                effective_autocomplete_attribute.value
        )
        super().__init__(*args, **kwargs)
