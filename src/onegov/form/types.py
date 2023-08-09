from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.form import Form
    from markupsafe import Markup
    from typing import Any, Literal, Protocol
    from typing_extensions import TypeAlias
    from webob.request import _FieldStorageWithFile
    from wtforms import Field, Form as BaseForm

    class Widget(Protocol):
        def __call__(self, field: 'Field', **kwargs: Any) -> Markup: ...

    Filter: TypeAlias = Callable[[Any], Any]
    BaseValidator: TypeAlias = Callable[[BaseForm, Field], object]
    Validator: TypeAlias = Callable[[Form, Field], object] | BaseValidator
    RawPricing: TypeAlias = tuple[float, str] | tuple[float, str, bool]
    PricingRules: TypeAlias = dict[str | range, RawPricing]
    SubmissionState: TypeAlias = Literal['pending', 'complete']
    RegistrationState: TypeAlias = Literal[
        'open', 'cancelled', 'confirmed', 'partial'
    ]
    # this matches what webob.request.POST returns as value type
    RawFormValue: TypeAlias = str | _FieldStorageWithFile
