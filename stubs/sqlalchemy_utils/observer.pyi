from _typeshed import Incomplete
from collections.abc import Callable, Collection, Iterable, Iterator
from sqlalchemy.orm import Mapper, Session
from sqlalchemy.orm.session import UOWTransaction  # type:ignore[attr-defined]
from typing import Any, NamedTuple
from typing_extensions import Never, TypeAlias

_CallbackArgs: TypeAlias = tuple[Any, Callable[..., Any], list[Any]]

class Callback(NamedTuple):
    func: Callable[..., Any]
    backref: Incomplete | None
    fullpath: list[Incomplete]

class PropertyObserver:
    listener_args: list[tuple[type[Any], str, Callable[..., Any]]]
    callback_map: dict[type[Any], list[Callback]]
    generator_registry: dict[type[Any], list[Callable[..., Any]]]
    def __init__(self) -> None: ...
    def remove_listeners(self) -> None: ...
    def register_listeners(self) -> None: ...
    def update_generator_registry(self, mapper: Mapper, class_: type[object]) -> None: ...
    def gather_paths(self) -> None: ...
    def gather_callback_args(self, obj: Any, callbacks: Iterable[Callback]) -> Iterator[_CallbackArgs]: ...
    def get_callback_args(self, root_obj: Any, callback: Callback) -> _CallbackArgs: ...
    def iterate_objects_and_callbacks(self, session: Session) -> Iterator[tuple[Any, list[Callback]]]: ...
    def invoke_callbacks(self, session: Session, ctx: UOWTransaction, instances: Collection[Any] | None) -> None: ...

# we don't want anyone to call this, call the scoped observers' observes instead
def observes(*paths: Never, **observer_kw: Never) -> Never: ...
