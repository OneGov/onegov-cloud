from __future__ import annotations

from inspect import getmembers

from wtforms.validators import DataRequired

from onegov.form.fields import UploadField
from onegov.form.validators import StrictOptional


from typing import overload, Any, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterator
    from onegov.form import Form
    from typing import TypeGuard
    from wtforms.fields.core import UnboundField

_FormT = TypeVar('_FormT', bound='Form')


def prepare_for_submission(
        form_class: type[_FormT],
        for_change_request: bool = False,
        force_simple: bool = True,
) -> type[_FormT]:
    # force all upload fields to be simple, we do not support the more
    # complex add/keep/replace widget, which is hard to properly support
    # and is not super useful in submissions
    def is_upload(attribute: object) -> TypeGuard[UnboundField[UploadField]]:
        if not hasattr(attribute, 'field_class'):
            return False

        return issubclass(attribute.field_class, UploadField)

    for name, field in getmembers(form_class, predicate=is_upload):

        if force_simple:
            if 'render_kw' not in field.kwargs:
                field.kwargs['render_kw'] = {}

            field.kwargs['render_kw']['force_simple'] = True

        # Otherwise the user gets stuck when in form validation not
        # changing the file
        if for_change_request:
            validators = [StrictOptional()] + [
                v for v in field.kwargs['validators'] or []
                if not isinstance(v, DataRequired)
            ]
            field.kwargs['validators'] = validators

    return form_class


@overload
def get_fields(
    form_class: type[Form],
    names_only: Literal[False] = False,
    exclude: Collection[str] | None = None
) -> Iterator[tuple[str, UnboundField[Any]]]: ...


@overload
def get_fields(
    form_class: type[Form],
    names_only: Literal[True],
    exclude: Collection[str] | None = None
) -> Iterator[str]: ...


def get_fields(
    form_class: type[Form],
    names_only: bool = False,
    exclude: Collection[str] | None = None
) -> Iterator[str | tuple[str, UnboundField[Any]]]:
    """ Takes an unbound form and returns the name of the fields """
    def is_field(attribute: object) -> TypeGuard[UnboundField[Any]]:
        return hasattr(attribute, 'field_class')

    for name, field in getmembers(form_class, predicate=is_field):
        if exclude and name in exclude:
            continue
        if names_only:
            yield name
        else:
            yield name, field
