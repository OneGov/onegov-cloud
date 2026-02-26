from __future__ import annotations

from contextlib import contextmanager
from html import escape
from onegov.form import errors
from onegov.form.core import FieldDependency
from onegov.form.core import Form
from onegov.form.fields import (
    MultiCheckboxField, DateTimeLocalField, URLField, VideoURLField)
from onegov.form.fields import TimeField, UploadField, UploadMultipleField
from onegov.form.parser.core import parse_formcode
from onegov.form.utils import as_internal_id
from onegov.form.validators import LaxDataRequired
from onegov.form.validators import ExpectedExtensions
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import If
from onegov.form.validators import Stdnum
from onegov.form.validators import StrictOptional
from onegov.form.validators import ValidDateRange
from onegov.form.widgets import DateRangeInput
from onegov.form.widgets import DateTimeLocalRangeInput
from wtforms.fields import DateField
from wtforms.fields import DecimalField
from wtforms.fields import EmailField
from wtforms.fields import IntegerField
from wtforms.fields import PasswordField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import Email
from wtforms.validators import Length
from wtforms.validators import NumberRange
from wtforms.validators import Regexp
from wtforms.validators import URL


from typing import overload, Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.form.parser.core import ParsedField
    from onegov.form.types import PricingRules, Validator, Widget
    from wtforms import Field as WTField

_FormT = TypeVar('_FormT', bound=Form)


MEGABYTE = 1000 ** 2
DEFAULT_UPLOAD_LIMIT = 100 * MEGABYTE


@overload
def parse_form(
    text: str,
    enable_edit_checks: bool,
    base_class: type[_FormT]
) -> type[_FormT]: ...


@overload
def parse_form(
    text: str,
    enable_edit_checks: bool = False,
    *,
    base_class: type[_FormT]
) -> type[_FormT]: ...


@overload
def parse_form(
    text: str,
    enable_edit_checks: bool = False,
    base_class: type[Form] = Form
) -> type[Form]: ...


def parse_form(
    text: str,
    enable_edit_checks: bool = False,
    base_class: type[Form] = Form
) -> type[Form]:
    """ Takes the given form text, parses it and returns a WTForms form
    class (not an instance of it).

    :type text: string form text to be parsed
    :param enable_edit_checks: bool to activate additional checks after
    editing a form.
    :param base_class: Form base class
    """

    builder = WTFormsClassBuilder(base_class)

    for fieldset in parse_formcode(text, enable_edit_checks):
        builder.set_current_fieldset(fieldset.label)

        for field in fieldset.fields:
            handle_field(builder, field)

    form_class = builder.form_class
    form_class._source = text

    return form_class


def handle_field(
    builder: WTFormsClassBuilder[Any],
    field: ParsedField,
    dependency: FieldDependency | None = None
) -> None:
    """ Takes the given parsed field and adds it to the form. """

    validators: list[Validator[Any, Any]]
    widget: Widget[Any] | None
    if field.type == 'text':
        render_kw = None
        if field.maxlength:
            validators = [Length(max=field.maxlength)]
            render_kw = {'data-max-length': field.maxlength}
        else:
            validators = []

        if field.regex:
            validators.append(Regexp(field.regex))

        builder.add_field(
            field_class=StringField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=validators,
            render_kw=render_kw,
            description=field.field_help
        )

    elif field.type == 'textarea':
        builder.add_field(
            field_class=TextAreaField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            render_kw={'rows': field.rows} if field.rows else None,
            description=field.field_help
        )

    elif field.type == 'password':
        builder.add_field(
            field_class=PasswordField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            description=field.field_help
        )

    elif field.type == 'email':
        builder.add_field(
            field_class=EmailField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[Email()],
            description=field.field_help
        )

    elif field.type == 'url':
        builder.add_field(
            field_class=URLField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[URL()],
            description=field.field_help
        )

    elif field.type == 'video_url':
        builder.add_field(
            field_class=VideoURLField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[URL()],
            description=field.field_help
        )

    elif field.type == 'stdnum':
        builder.add_field(
            field_class=StringField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[Stdnum(field.format)],
            description=field.field_help
        )

    elif field.type == 'date':
        widget = None
        validators = []
        if field.valid_date_range:
            start = field.valid_date_range.start
            stop = field.valid_date_range.stop
            widget = DateRangeInput(start, stop)
            validators.append(ValidDateRange(start, stop))

        builder.add_field(
            field_class=DateField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            description=field.field_help,
            validators=validators,
            widget=widget
        )

    elif field.type == 'datetime':
        widget = None
        validators = []
        if field.valid_date_range:
            start = field.valid_date_range.start
            stop = field.valid_date_range.stop
            widget = DateTimeLocalRangeInput(start, stop)
            validators.append(ValidDateRange(start, stop))

        builder.add_field(
            field_class=DateTimeLocalField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            description=field.field_help,
            validators=validators,
            widget=widget
        )

    elif field.type == 'time':
        builder.add_field(
            field_class=TimeField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            description=field.field_help
        )

    elif field.type == 'fileinput':
        expected_extensions = ExpectedExtensions(field.extensions)
        # build an accept attribute for the file input
        accept = ','.join(expected_extensions.whitelist)
        builder.add_field(
            field_class=UploadField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[
                FileSizeLimit(DEFAULT_UPLOAD_LIMIT)
            ],
            allowed_mimetypes=expected_extensions.whitelist,
            render_kw={'accept': accept},
            description=field.field_help
        )

    elif field.type == 'multiplefileinput':
        expected_extensions = ExpectedExtensions(field.extensions)
        # build an accept attribute for the file input
        accept = ','.join(expected_extensions.whitelist)
        builder.add_field(
            field_class=UploadMultipleField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[
                FileSizeLimit(DEFAULT_UPLOAD_LIMIT)
            ],
            allowed_mimetypes=expected_extensions.whitelist,
            render_kw={'accept': accept},
            description=field.field_help
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
            pricing=field.pricing,
            discount=field.discount,
            # do not coerce None into 'None'
            coerce=lambda v: str(v) if v is not None else v,
            description=field.field_help
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
            pricing=field.pricing,
            discount=field.discount,
            # do not coerce None into 'None'
            coerce=lambda v: str(v) if v is not None else v,
            description=field.field_help
        )

    elif field.type == 'integer_range':
        builder.add_field(
            field_class=IntegerField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            pricing=field.pricing,
            validators=[
                NumberRange(
                    field.range.start,
                    field.range.stop
                )
            ],
            description=field.field_help
        )

    elif field.type == 'decimal_range':
        builder.add_field(
            field_class=DecimalField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[
                NumberRange(
                    field.range.start,
                    field.range.stop
                )
            ],
            description=field.field_help
        )

    elif field.type == 'chip_nr':
        builder.add_field(
            field_class=StringField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            validators=[Regexp(r'^[0-9]{15}$')],
            description=field.field_help
        )

    elif field.type == 'code':
        builder.add_field(
            field_class=TextAreaField,
            field_id=field.id,
            label=field.label,
            dependency=dependency,
            required=field.required,
            render_kw={'data-editor': field.syntax},
            description=field.field_help
        )

    else:
        raise NotImplementedError

    if field.type == 'radio' or field.type == 'checkbox':
        for choice in field.choices:
            if not choice.fields:
                continue

            with builder.handle_nested_fieldset(choice.fieldset):
                dependency = FieldDependency(field.id, choice.key)
                for choice_field in choice.fields:
                    handle_field(builder, choice_field, dependency)


class WTFormsClassBuilder(Generic[_FormT]):
    """ Helps dynamically build a wtforms class from parsed blocks.

    For example::

        builder = WTFormsClassBuilder(BaseClass)
        builder.add_field(StringField, label='Name', required=True)

        MyForm = builder.form_class
    """

    form_class: type[_FormT]
    current_fieldset: str | None

    def __init__(self, base_class: type[_FormT]):

        class DynamicForm(base_class):  # type:ignore
            # NOTE: The way we build field dependencies is not quite
            #       the same as for manual dependencies, so this method
            #       will not work for field dependencies from nested
            #       fields
            def is_visible_through_dependencies(self, field_id: str) -> bool:
                if not super().is_visible_through_dependencies(field_id):
                    return False

                field = self[field_id]
                dependency = (field.render_kw or {}).get('data-depends-on')
                if not dependency:
                    return True

                # NOTE: This shouldn't happen for fields created from form code
                if ';' in dependency:
                    return False

                field_id, value = dependency.split('/', 1)
                if field_id not in self or self[field_id].data != value:
                    return False

                return self.is_visible_through_dependencies(field_id)

        self.form_class = DynamicForm
        self.current_fieldset = None

    def set_current_fieldset(self, label: str | None) -> None:
        self.current_fieldset = label

    @contextmanager
    def handle_nested_fieldset(self, label: str | None) -> Iterator[None]:
        if label is None:
            yield None
            return

        old_fieldset = self.current_fieldset
        self.current_fieldset = label
        try:
            yield
        finally:
            self.current_fieldset = old_fieldset

    def validators_extend(
        self,
        validators: list[Validator[Any, Any]],
        required: bool,
        dependency: FieldDependency | None
    ) -> None:
        if required:
            if dependency is None:
                self.validators_add_required(validators)
            else:
                self.validators_add_dependency(validators, dependency)
        else:
            self.validators_add_optional(validators)

    def validators_add_required(
        self,
        validators: list[Validator[Any, Any]]
    ) -> None:
        # we use the DataRequired check instead of InputRequired, since
        # InputRequired only works if the data comes over the wire. We
        # also want to load forms with data from the database, where
        # InputRequired will fail, but DataRequired will not.
        #
        # As a consequence, falsey values can't be submitted for now.
        validators.insert(0, LaxDataRequired())

    def validators_add_dependency(
        self,
        validators: list[Validator[Any, Any]],
        dependency: FieldDependency
    ) -> None:
        # if the dependency is not fulfilled, the field may be empty
        # but it must still validate otherwise (invalid = nok, empty = ok)
        validator = If(dependency.unfulfilled, StrictOptional())
        validator.field_flags = {'required': True}  # type:ignore[attr-defined]
        validators.insert(0, validator)

        # if the dependency is fulfilled, the field is required
        validator = If(dependency.fulfilled, LaxDataRequired())
        validator.field_flags = {'required': True}  # type:ignore[attr-defined]
        validators.insert(0, validator)

    def validators_add_optional(
        self,
        validators: list[Validator[Any, Any]]
    ) -> None:
        validators.insert(0, StrictOptional())

    def mark_as_dependent(
        self,
        field_id: str,
        dependency: FieldDependency
    ) -> None:

        field = getattr(self.form_class, field_id)
        if not field.kwargs.get('render_kw'):
            field.kwargs['render_kw'] = {}
        field.kwargs['render_kw'].update(dependency.html_data(''))

    def get_unique_field_id(
        self,
        label: str,
        dependency: FieldDependency | None
    ) -> str:
        # try to find a smart field_id that contains the dependency or the
        # current fieldset name - if all fails, an error will be thrown,
        # as field_ids *need* to be unique
        if dependency:
            field_id = dependency.field_id + '_' + as_internal_id(label)
        elif self.current_fieldset:
            field_id = as_internal_id(self.current_fieldset + ' ' + label)
        else:
            field_id = as_internal_id(label)

        if hasattr(self.form_class, field_id):
            raise errors.DuplicateLabelError(label=label)

        return field_id

    def add_field(
        self,
        field_class: type[WTField],
        field_id: str,
        label: str,
        required: bool,
        dependency: FieldDependency | None = None,
        pricing: PricingRules | None = None,
        validators: list[Validator[Any, Any]] | None = None,
        description: str | None = None,
        widget: Widget[Any] | None = None,
        render_kw: dict[str, Any] | None = None,
        # for field classes that have more than just the base arguments
        **extra_field_kwargs: Any
    ) -> WTField:
        validators = validators or []

        if hasattr(self.form_class, field_id):
            raise errors.DuplicateLabelError(label=label)

        # labels in wtforms are not escaped correctly - for safety we make sure
        # that the label is properly html escaped. See also:
        # https://github.com/wtforms/wtforms/issues/315
        # -> quotes are allowed because the label is rendered between tags,
        # not as part of the attributes
        label = type(label)(escape(label, quote=False))

        self.validators_extend(validators, required, dependency)

        setattr(self.form_class, field_id, field_class(
            label=label,
            validators=validators,
            fieldset=self.current_fieldset,
            pricing=pricing,
            description=description or '',
            widget=widget,
            render_kw=render_kw,
            **extra_field_kwargs
        ))

        if dependency:
            self.mark_as_dependent(field_id, dependency)

        return getattr(self.form_class, field_id)
