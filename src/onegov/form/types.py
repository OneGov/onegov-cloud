from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING

BaseFormT = TypeVar('BaseFormT', bound='BaseForm', contravariant=True)
FormT = TypeVar('FormT', bound='Form', contravariant=True)
FieldT = TypeVar('FieldT', bound='Field', contravariant=True)

if TYPE_CHECKING:
    from onegov.form import Form
    from typing import Any, Literal, Protocol, TypeAlias
    from webob.request import _FieldStorageWithFile
    from wtforms.fields.core import _Filter, _Validator, _Widget, Field
    from wtforms.form import BaseForm

    class FieldCondition(Protocol[BaseFormT, FieldT]):
        def __call__(self, form: BaseFormT, field: FieldT, /) -> bool: ...

    Widget: TypeAlias = _Widget
    Filter: TypeAlias = _Filter
    BaseValidator: TypeAlias = _Validator
    # validator is slightly more specific in that it expects our Form type
    Validator: TypeAlias = _Validator[FormT, FieldT]
    Validators: TypeAlias = tuple[_Validator[FormT, FieldT], ...] | list[Any]
    RawPricing: TypeAlias = tuple[float, str] | tuple[float, str, bool]
    PricingRules: TypeAlias = dict[str | range, RawPricing]
    SubmissionState: TypeAlias = Literal['pending', 'complete']
    RegistrationState: TypeAlias = Literal[
        'open', 'cancelled', 'confirmed', 'partial'
    ]
    # this matches what webob.request.POST returns as value type
    RawFormValue: TypeAlias = str | _FieldStorageWithFile
