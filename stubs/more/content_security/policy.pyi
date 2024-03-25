from collections.abc import Callable, Iterator
from typing import Any, Generic, TypeVar, overload
from typing_extensions import Self, TypeAlias, TypeGuard

from webob.response import Response

_T = TypeVar('_T')
_Type: TypeAlias = type[_T]

SELF: str
UNSAFE_INLINE: str
UNSAFE_EVAL: str
NONE: str
STRICT_DYNAMIC: str

class Directive(Generic[_T]):
    name: str
    type: _Type[_T]
    default: Callable[[], _T]
    renderer: Callable[[_T], str | None]
    def __init__(self, name: str, type: _Type[_T], default: Callable[[], _T], render: Callable[[_T], str]) -> None: ...
    def render(self, instance: ContentSecurityPolicy) -> str | None: ...
    @overload
    def __get__(self, instance: None, cls: _Type[ContentSecurityPolicy]) -> Self: ...
    @overload
    def __get__(self, instance: ContentSecurityPolicy, cls: _Type[ContentSecurityPolicy]) -> _T: ...
    def __set__(self, instance: ContentSecurityPolicy, value: _T) -> None: ...

class SetDirective(Directive[set[str]]):
    def __init__(self, name: str) -> None: ...

class SingleValueDirective(Directive[str]):
    def __init__(self, name: str) -> None: ...

class BooleanDirective(Directive[bool]):
    def __init__(self, name: str) -> None: ...

def is_directive(obj: object) -> TypeGuard[Directive[Any]]: ...
def render_set(value: set[str]) -> str: ...
def render_bool(value: bool) -> str | None: ...

class ContentSecurityPolicy:
    child_src: SetDirective
    connect_src: SetDirective
    default_src: SetDirective
    font_src: SetDirective
    frame_src: SetDirective
    img_src: SetDirective
    manifest_src: SetDirective
    media_src: SetDirective
    object_src: SetDirective
    script_src: SetDirective
    style_src: SetDirective
    worker_src: SetDirective
    base_uri: SetDirective
    plugin_types: SetDirective
    sandbox: SingleValueDirective
    disown_opener: BooleanDirective
    form_action: SetDirective
    frame_ancestors: SetDirective
    report_uri: SingleValueDirective
    report_to: SingleValueDirective
    block_all_mixed_content: BooleanDirective
    require_sri_for: SingleValueDirective
    upgrade_insecure_requeists: BooleanDirective
    report_only: bool
    def __init__(
        self,
        report_only: bool = False,
        *,
        child_src: set[str] = ...,
        connect_src: set[str] = ...,
        default_src: set[str] = ...,
        font_src: set[str] = ...,
        frame_src: set[str] = ...,
        img_src: set[str] = ...,
        manifest_src: set[str] = ...,
        media_src: set[str] = ...,
        object_src: set[str] = ...,
        script_src: set[str] = ...,
        style_src: set[str] = ...,
        worker_src: set[str] = ...,
        base_uri: set[str] = ...,
        plugin_types: set[str] = ...,
        sandbox: str = ...,
        disown_opener: bool = False,
        form_action: set[str] = ...,
        frame_ancestors: set[str] = ...,
        report_uri: str = ...,
        report_to: str = ...,
        block_all_mixed_content: bool = False,
        require_sri_for: str = ...,
        upgrade_insecure_requeists: bool = False,
        **directives: set[str] | str | bool
    ) -> None: ...
    def copy(self) -> Self: ...
    @property
    def directives(self) -> Iterator[SetDirective | SingleValueDirective | BooleanDirective]: ...
    @property
    def text(self) -> str: ...
    @property
    def header_name(self) -> str: ...
    def apply(self, response: Response) -> None: ...
