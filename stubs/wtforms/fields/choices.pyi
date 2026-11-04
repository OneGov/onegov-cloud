from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from enum import Enum, EnumMeta
from typing import Any, Literal, NamedTuple, TypeAlias, TypeVar
from typing_extensions import Self

from wtforms.datalist import DataList
from wtforms.fields.core import Field, _Filter, _FormT, _Validator, _Widget
from wtforms.form import BaseForm
from wtforms.meta import DefaultMeta, _SupportsGettextAndNgettext

from onegov.form.types import PricingRules

__all__ = ("SelectField", "Choice", "SelectChoice", "SelectMultipleField", "RadioField")

_FieldT = TypeVar("_FieldT", bound=Field)
_Option: TypeAlias = SelectFieldBase._Option
# For the two argument callback the implementation might depend on a specific form class
# which is perfectly valid, but since parameter types are contravariant, we cannot restrict
# the callback to `BaseForm`, so we use `Any` instead. We could perhaps use the same trick
# as with _Validators leveraging a `Protocol` with an unbound contravariant type parameter
# but I'm not sure it's worth the extra complexity.
_AnyForm: TypeAlias = Any
_SelectChoicesCallback: TypeAlias = Callable[[_AnyForm, _FieldT], Sequence[SelectChoice]] | Callable[[], Sequence[SelectChoice]]

class Choice(NamedTuple):
    value: str
    label: str
    selected: bool
    render_kw: dict[str, Any]

@dataclass
class SelectChoice:
    value: str
    label: str = ...
    render_kw: dict[str, Any] = ...
    optgroup: str | None = ...
    def __post_init__(self) -> None: ...
    def __iter__(self) -> Iterator[tuple[str, str, dict[str, Any], str | None]]: ...
    @classmethod
    def from_input(
        cls,
        input: SelectChoice | tuple[str, str | None] | tuple[str, str | None, dict[str, Any]] | str,
        optgroup: str | None = None,
    ) -> Self: ...

# we could make these generic, but it's not really worth it
def enum_choices(
    enum_cls: EnumMeta, *, by: Literal["name", "value"] = "value", label: Callable[[Any], str] | None = None
) -> list[SelectChoice]: ...
def enum_coerce(enum_cls: EnumMeta, *, by: Literal["name", "value"] = "value") -> Callable[[Any], Enum]: ...

class SelectFieldBase(Field):
    option_widget: _Widget[_Option]
    def __init__(
        self,
        label: str | None = None,
        validators: tuple[_Validator[_FormT, Self], ...] | list[Any] | None = None,
        option_widget: _Widget[_Option] | None = None,
        *,
        filters: Sequence[_Filter] = (),
        description: str = "",
        id: str | None = None,
        default: object | None = None,
        invalid_value_message: str | None = None,
        widget: _Widget[Self] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        datalist: DataList | str | None = None,
        _form: BaseForm | None = None,
        _prefix: str = "",
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
        discount: dict[str, float] | None = None,
    ) -> None: ...
    def iter_choices(self) -> Iterator[Choice]: ...
    def has_groups(self) -> bool: ...
    def iter_groups(self) -> Iterator[tuple[str, list[Choice]]]: ...
    def __iter__(self) -> Iterator[_Option]: ...

    class _Option(Field):
        checked: bool

class SelectField(SelectFieldBase):
    _choices_stale: bool
    coerce: Callable[[Any], Any]
    validate_choice: bool
    invalid_choice_message: str
    def __init__(
        self,
        label: str | None = None,
        validators: tuple[_Validator[_FormT, Self], ...] | list[Any] | None = None,
        coerce: Callable[[Any], Any] = ...,
        choices: Iterable[SelectChoice] | _SelectChoicesCallback[Self] | None = None,
        validate_choice: bool = True,
        invalid_value_message: str | None = None,
        invalid_choice_message: str | None = None,
        *,
        filters: Sequence[_Filter] = (),
        description: str = "",
        id: str | None = None,
        default: object | None = None,
        widget: _Widget[Self] | None = None,
        option_widget: _Widget[SelectFieldBase._Option] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        datalist: DataList | str | None = None,
        _form: BaseForm | None = None,
        _prefix: str = "",
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
        discount: dict[str, float] | None = None,
    ) -> None: ...

    @property
    def choices(self) -> Sequence[SelectChoice]: ...
    @choices.setter
    def choices(self, value: Iterable[SelectChoice] | _SelectChoicesCallback[Self]) -> None: ...

class SelectMultipleField(SelectField):
    data: list[Any] | None

class RadioField(SelectField):
    def __init__(
        self,
        label: str | None = None,
        validators: tuple[_Validator[_FormT, Self], ...] | list[Any] | None = None,
        *,
        option_widget: _Widget[_Option] | None = None,
        coerce: Callable[[Any], Any] = ...,
        choices: Iterable[SelectChoice] | _SelectChoicesCallback[Self] | None = None,
        validate_choice: bool = True,
        invalid_value_message: str | None = None,
        invalid_choice_message: str | None = None,
        filters: Sequence[_Filter] = (),
        description: str = "",
        id: str | None = None,
        default: object | None = None,
        widget: _Widget[Self] | None = None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        datalist: DataList | str | None = None,
        _form: BaseForm | None = None,
        _prefix: str = "",
        _translations: _SupportsGettextAndNgettext | None = None,
        _meta: DefaultMeta | None = None,
        # onegov specific kwargs that get popped off
        fieldset: str | None = None,
        depends_on: Sequence[Any] | None = None,
        pricing: PricingRules | None = None,
        discount: dict[str, float] | None = None,
    ) -> None: ...
