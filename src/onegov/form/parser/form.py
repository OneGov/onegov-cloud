from __future__ import annotations

from decimal import Decimal
from html import escape
from functools import cached_property
from io import StringIO
from onegov.form import errors, log
from onegov.form.core import Form
from onegov.form.fields import (
    MultiCheckboxField, DateTimeLocalField, URLField, VideoURLField)
from onegov.form.fields import TimeField, UploadField, UploadMultipleField
from onegov.form.parser.core import flatten_fields, parse_formcode, ParsedField
from onegov.form.validators import LaxDataRequired
from onegov.form.validators import ExpectedExtensions
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import Stdnum
from onegov.form.validators import StrictOptional
from onegov.form.validators import ValidDateRange
from onegov.form.widgets import DateRangeInput
from onegov.form.widgets import DateTimeLocalRangeInput
from pydantic import BaseModel, ConfigDict, Field
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


from typing import Any, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form.types import PricingRules, Validator, Widget
    from wtforms.fields.core import Field as WTField


MEGABYTE = 1000 ** 2
DEFAULT_UPLOAD_LIMIT = 100 * MEGABYTE


class ParsedForm(BaseModel):
    """
    Represents a parsed form.
    """

    model_config = ConfigDict(frozen=True)

    fields: tuple[ParsedField, ...]
    source_code: str | None = Field(
        default=None,
        description='The original formcode that was parsed to generate '
            'this structure. Leave empty, when directly generating a '
            'form structure. This is mostly useful for preserving '
            'formatting, when editing the form via formcode. As long as '
            'this successfully parses back into the same structure, we will '
            'pre-fill the edit field with this text, instead of generating '
            'formcode based on the structure.'
    )

    @cached_property
    def flattened_fields(self) -> tuple[ParsedField, ...]:
        return tuple(flatten_fields(self.fields))

    @cached_property
    def formcode(self) -> str:
        return self.source_code or self.to_formcode()

    # NOTE: Ideally we only access this when editing formcode, since it
    #       can be very expensive. If we don't want to ensure that the
    #       formcode is still valid, we can just access source_code.
    @cached_property
    def safe_formcode(self) -> str:
        if self.source_code is not None:
            try:
                if self.fields == tuple(parse_formcode(
                    self.source_code,
                    enable_edit_checks=True
                )):
                    return self.source_code
            except Exception:
                log.warning(
                    f'Failed to parse stored formcode:\n{self.source_code}'
                )
        return self.to_formcode()

    def to_formcode(self) -> str:
        fieldset: str | None = None
        buffer = StringIO()
        first_line = True
        for field in self.fields:
            if field.fieldset != fieldset:
                if not first_line:
                    # insert an extra newline above the fieldset
                    buffer.write('\n')
                fieldset = field.fieldset
                # if we encounter an anonymous fieldset after a
                # named one we need to display it as `...`
                buffer.write(f'# {'...' if fieldset is None else fieldset}\n')
            field.write_formcode(buffer, '')
            first_line = False
        return buffer.getvalue()

    def form_class[T: Form = Form](
        self,
        base_class: type[T] = Form  # type: ignore[assignment]
    ) -> type[T]:

        # NOTE: Since ParsedForm is intended to be immutable, we can
        #       cache the generated form class per base class.
        cache = self.__dict__.setdefault('_form_class', {})
        cached = cache.get(base_class)
        if cached is not None:
            return cached

        builder = WTFormsClassBuilder(base_class)

        for field in self.fields:
            handle_field(builder, field)

        form_class = cache[base_class] = builder.form_class
        form_class._parsed = self
        form_class._source = self.source_code or self.to_formcode()

        return form_class

    @classmethod
    def from_formcode(
        cls,
        definition: str,
        # FIXME: Eventually we want these to always be enabled
        #        so we can get rid of this parameter again
        enable_edit_checks: bool = False
    ) -> Self:
        return cls.model_construct(
            fields=tuple(parse_formcode(definition, enable_edit_checks)),
            source_code=definition
        )


# FIXME: We can probably get rid of this function and instead just
#        rely on `ParsedForm`.
def parse_form[T: Form = Form](
    text: str,
    enable_edit_checks: bool = False,
    base_class: type[T] = Form  # type: ignore[assignment]
) -> type[T]:
    """ Takes the given form text, parses it and returns a WTForms form
    class (not an instance of it).

    :type text: string form text to be parsed
    :param enable_edit_checks: bool to activate additional checks after
    editing a form.
    :param base_class: Form base class
    """

    parsed = ParsedForm.from_formcode(text, enable_edit_checks)
    return parsed.form_class(base_class)


def handle_field(
    builder: WTFormsClassBuilder[Any],
    field: ParsedField,
    depends_on: tuple[str, str] | None = None,
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
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            validators=validators,
            render_kw=render_kw,
            description=field.field_help
        )

    elif field.type == 'textarea':
        builder.add_field(
            field_class=TextAreaField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            render_kw={'rows': field.rows} if field.rows else None,
            description=field.field_help
        )

    elif field.type == 'password':
        builder.add_field(
            field_class=PasswordField,
            field_id=field.id,
            fieldset=field.real_fieldset,
            label=field.display_label,
            depends_on=depends_on,
            required=field.required,
            description=field.field_help
        )

    elif field.type == 'email':
        builder.add_field(
            field_class=EmailField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            validators=[Email()],
            description=field.field_help
        )

    elif field.type == 'url':
        builder.add_field(
            field_class=URLField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            validators=[URL()],
            description=field.field_help
        )

    elif field.type == 'video_url':
        builder.add_field(
            field_class=VideoURLField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            validators=[URL()],
            description=field.field_help
        )

    elif field.type == 'stdnum':
        builder.add_field(
            field_class=StringField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
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
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
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
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            description=field.field_help,
            validators=validators,
            widget=widget
        )

    elif field.type == 'time':
        builder.add_field(
            field_class=TimeField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
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
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            validators=[
                FileSizeLimit(DEFAULT_UPLOAD_LIMIT)
            ],
            allowed_mimetypes=expected_extensions.whitelist,
            render_kw={'accept': accept, 'resend_upload': True},
            description=field.field_help
        )

    elif field.type == 'multiplefileinput':
        expected_extensions = ExpectedExtensions(field.extensions)
        # build an accept attribute for the file input
        accept = ','.join(expected_extensions.whitelist)
        builder.add_field(
            field_class=UploadMultipleField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            validators=[
                FileSizeLimit(DEFAULT_UPLOAD_LIMIT)
            ],
            allowed_mimetypes=expected_extensions.whitelist,
            render_kw={'accept': accept, 'resend_upload': True},
            description=field.field_help
        )

    elif field.type == 'radio':
        builder.add_field(
            field_class=RadioField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            choices=[(c.label, c.display_label) for c in field.choices],
            default=next((c.label for c in field.choices if c.selected), None),
            pricing={
                c.label: c.pricing.as_tuple()
                for c in field.choices
                if c.pricing is not None
            } or None,
            discount={
                c.label: c.discount / Decimal('100')
                for c in field.choices
                if c.discount is not None
            } or None,
            # do not coerce None into 'None'
            coerce=lambda v: str(v) if v is not None else v,
            description=field.field_help
        )

    elif field.type == 'checkbox':
        builder.add_field(
            field_class=MultiCheckboxField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            choices=[(c.label, c.display_label) for c in field.choices],
            default=[c.label for c in field.choices if c.selected],
            pricing={
                c.label: c.pricing.as_tuple()
                for c in field.choices
                if c.pricing is not None
            } or None,
            discount={
                c.label: c.discount / Decimal('100')
                for c in field.choices
                if c.discount is not None
            } or None,
            # do not coerce None into 'None'
            coerce=lambda v: str(v) if v is not None else v,
            description=field.field_help
        )

    elif field.type == 'integer_range':
        builder.add_field(
            field_class=IntegerField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            pricing={
                range(
                    field.range.start,
                    field.range.stop
                ): field.pricing_per_item.as_tuple()
            } if field.pricing_per_item is not None else None,
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
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
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
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            validators=[Regexp(r'^[0-9]{15}$')],
            description=field.field_help
        )

    elif field.type == 'code':
        builder.add_field(
            field_class=TextAreaField,
            field_id=field.id,
            label=field.display_label,
            fieldset=field.real_fieldset,
            depends_on=depends_on,
            required=field.required,
            render_kw={'data-editor': field.syntax},
            description=field.field_help
        )

    else:
        raise NotImplementedError

    if field.type == 'radio' or field.type == 'checkbox':
        # NOTE: We have to walk the subfields in a specific order in order
        #       to make sure we don't create too many fieldsets
        subfield_stacks = [
            (choice, list(reversed(choice.fields)))
            for choice in field.choices
            if choice.fields
        ]
        if not subfield_stacks:
            return

        current_fieldset = field.real_fieldset
        branch_index = 0
        for _ in range(sum(len(stack) for _, stack in subfield_stacks)):
            for idx in range(branch_index, len(subfield_stacks)):
                choice, stack = subfield_stacks[idx]
                if stack and stack[-1].real_fieldset == current_fieldset:
                    branch_index = idx
                    subfield = stack.pop()
                    handle_field(
                        builder,
                        subfield,
                        depends_on=(field.id, choice.label)
                    )
                    break
            else:
                # none of the candidates match the current fieldset
                # go back to the first non-empty branch and update
                # the current fieldset
                for idx, (choice, stack) in enumerate(subfield_stacks):
                    if stack:
                        branch_index = idx
                        subfield = stack.pop()
                        current_fieldset = subfield.real_fieldset
                        handle_field(
                            builder,
                            subfield,
                            depends_on=(field.id, choice.label)
                        )
                        break

        # NOTE: Sanity check to make sure we depleted all of the stacks
        assert all(not stack for _, stack in subfield_stacks)


class WTFormsClassBuilder[FormT: Form]:
    """ Helps dynamically build a wtforms class from parsed blocks.

    For example::

        builder = WTFormsClassBuilder(BaseClass)
        builder.add_field(StringField, label='Name', required=True)

        MyForm = builder.form_class
    """

    form_class: type[FormT]

    def __init__(self, base_class: type[FormT]):

        class DynamicForm(base_class):  # type:ignore
            pass

        self.form_class = DynamicForm

    def add_field(
        self,
        field_class: type[WTField],
        field_id: str,
        label: str,
        required: bool,
        fieldset: str | None,
        depends_on: tuple[str, str] | None = None,
        pricing: PricingRules | None = None,
        validators: list[Validator[Any, Any]] | None = None,
        description: str | None = None,
        widget: Widget[Any] | None = None,
        render_kw: dict[str, Any] | None = None,
        # for field classes that have more than just the base arguments
        **extra_field_kwargs: Any
    ) -> None:
        validators = validators or []

        if hasattr(self.form_class, field_id):
            raise errors.DuplicateLabelError(label=label)

        # labels in wtforms are not escaped correctly - for safety we make sure
        # that the label is properly html escaped. See also:
        # https://github.com/wtforms/wtforms/issues/315
        # -> quotes are allowed because the label is rendered between tags,
        # not as part of the attributes
        label = type(label)(escape(label, quote=False))
        validators.insert(
            0,
            LaxDataRequired() if required else StrictOptional()
        )

        setattr(self.form_class, field_id, field_class(
            label=label,
            validators=validators,
            fieldset=fieldset,
            pricing=pricing,
            description=description or '',
            widget=widget,
            render_kw=render_kw or {},
            depends_on=depends_on,
            **extra_field_kwargs
        ))
