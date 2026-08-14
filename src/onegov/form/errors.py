from __future__ import annotations

from onegov.form.i18n import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wtforms import Field


class FormError(Exception):

    def __repr__(self) -> str:
        return self.__class__.__name__


class InvalidMimeType(FormError):
    pass


class UnableToComplete(FormError):
    pass


class FormParsingError(FormError):
    message_template = _('The form could not be parsed.')

    def field_message(self, field: Field) -> str:
        return field.gettext(self.message_template)


class _FormParsingErrorWithLineContext(FormParsingError):

    def __init__(self, line: int):
        self.line = line

    def field_message(self, field: Field) -> str:
        return super().field_message(field).format(line=self.line)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(line={self.line})'


class InvalidFormSyntax(_FormParsingErrorWithLineContext):
    message_template = _('The syntax on line {line} is not valid.')


class InvalidIndentSyntax(_FormParsingErrorWithLineContext):
    message_template = _(
        'The indentation on line {line} is not valid. '
        'Please use a multiple of 4 spaces'
    )


class InvalidCommentIndentSyntax(_FormParsingErrorWithLineContext):
    message_template = _(
        'The indentation on line {line} is not valid. A comment must be '
        'indented to the same level as the field (`=`) or option group it '
        'describes.'
    )


class InvalidCommentLocationSyntax(_FormParsingErrorWithLineContext):
    message_template = _(
        'Incorrect placement of the field description on '
        'line {line}. The field description must be placed '
        'below the field definition (`=`) and with the same '
        'indentation.'
    )


class _FormParsingErrorWithLabelContext(FormParsingError):

    def __init__(self, label: str):
        self.label = label

    def field_message(self, field: Field) -> str:
        return super().field_message(field).format(label=self.label)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(label={self.label!r})'


class DuplicateLabelError(_FormParsingErrorWithLabelContext):
    message_template = _("The field '{label}' exists more than once.")


class EmptyFieldsetError(_FormParsingErrorWithLabelContext):
    message_template = _(
        "The '{label}' group is empty and will not be visible. Either remove "
        "the empty group or add fields to it."
    )


class FieldCompileError(_FormParsingErrorWithLabelContext):
    message_template = _(
        "The field '{label}' has no type defined. "
        "For example use '___' for a text field."
    )


class MixedTypeError(_FormParsingErrorWithLabelContext):
    message_template = _(
        "The field '{label}' cannot mix radio buttons and checkboxes."
    )
