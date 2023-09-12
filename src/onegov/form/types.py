from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
    from typing import Any, Literal, Protocol, TypeVar
    from typing_extensions import TypeAlias
    from webob.request import _FieldStorageWithFile
    from wtforms.fields.core import _Filter, _Validator, _Widget, Field
    from wtforms.form import BaseForm

    _BaseFormT = TypeVar('_BaseFormT', bound=BaseForm, contravariant=True)
    _FormT = TypeVar('_FormT', bound=Form, contravariant=True)
    _FieldT = TypeVar('_FieldT', bound=Field, contravariant=True)

    class FieldCondition(Protocol[_BaseFormT, _FieldT]):
        def __call__(self, __form: _BaseFormT, __field: _FieldT) -> bool: ...

    Widget: TypeAlias = _Widget
    Filter: TypeAlias = _Filter
    BaseValidator: TypeAlias = _Validator
    # validator is slightly more specific in that it expects our Form type
    Validator: TypeAlias = _Validator[_FormT, _FieldT]
    Validators: TypeAlias = tuple[_Validator[_FormT, _FieldT], ...] | list[Any]
    RawPricing: TypeAlias = tuple[float, str] | tuple[float, str, bool]
    PricingRules: TypeAlias = dict[str | range, RawPricing]
    SubmissionState: TypeAlias = Literal['pending', 'complete']
    RegistrationState: TypeAlias = Literal[
        'open', 'cancelled', 'confirmed', 'partial'
    ]
    # this matches what webob.request.POST returns as value type
    RawFormValue: TypeAlias = str | _FieldStorageWithFile
