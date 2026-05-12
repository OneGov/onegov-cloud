from __future__ import annotations

from typing import Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
    from typing import Any, Protocol
    from webob.request import _FieldStorageWithFile
    from wtforms.fields.core import _Filter, _Validator, _Widget, Field
    from wtforms.form import BaseForm

    class FieldCondition[BaseFormT: BaseForm, FieldT: Field](Protocol):
        def __call__(self, form: BaseFormT, field: FieldT, /) -> bool: ...

    type Widget[T: Field] = _Widget[T]
    type Filter = _Filter
    type BaseValidator[
        FormT: BaseForm,
        FieldT: Field
    ] = _Validator[FormT, FieldT]
    # validator is slightly more specific in that it expects our Form type
    type Validator[FormT: Form, FieldT: Field] = _Validator[FormT, FieldT]
    type Validators[
        FormT: Form,
        FieldT: Field
    ] = tuple[_Validator[FormT, FieldT], ...] | list[Any]
    type RawPricing = tuple[float, str] | tuple[float, str, bool]
    type PricingRules = dict[str | range, RawPricing]
    # this matches what webob.request.POST returns as value type
    type RawFormValue = str | _FieldStorageWithFile

type SubmissionState = Literal['pending', 'complete']
type RegistrationState = Literal[
    'open', 'cancelled', 'confirmed', 'partial'
]

FormT = TypeVar('FormT', bound='Form', contravariant=True)
FieldT = TypeVar('FieldT', bound='Field', contravariant=True)
