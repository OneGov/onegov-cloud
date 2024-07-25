from _typeshed.wsgi import WSGIEnvironment
from collections.abc import Callable
from dectate import Sentinel
from webob.request import BaseRequest
from webob.response import Response as BaseResponse
from typing import overload, Any, TypeVar

from morepath import reify
from morepath.app import App
from morepath.authentication import Identity, NoIdentity

_T = TypeVar('_T')
_AfterF = TypeVar('_AfterF', bound=Callable[[Response], Any])

SAME_APP: Sentinel

class Request(BaseRequest):
    # FIXME: These two attributes look like internal API of morepath, so
    #        if we don't use them it's easier to just pretend, they don't
    #        exist, but just in case we do use them, I will leave this
    #        comment
    # path_code_info: Incomplete
    # view_code_info: Incomplete
    unconsumed: list[str]
    app: App
    view_name: str  # this technically only exists after resolve_response
    def __init__(self, environ: WSGIEnvironment, app: App, **kw: Any) -> None: ...
    def reset(self) -> None: ...
    @reify
    def identity(self) -> Identity | NoIdentity: ...
    def link_prefix(self, app: App | None = None) -> str: ...
    def view(self, obj: object, default: _T | None = None, app: App | Sentinel = ..., **predicates: Any) -> Any | _T | None: ...
    @overload
    def link(self, obj: None, name: str = '', default: None = None, app: App | Sentinel = ...) -> None: ...
    @overload
    def link(self, obj: None, name: str, default: _T, app: App | Sentinel = ...) -> _T: ...
    @overload
    def link(self, obj: object, name: str = '', default: Any = None, app: App | Sentinel = ...) -> str: ...
    def class_link(self, model: type, variables: dict[str, Any] | None = None, name: str = '', app: App | Sentinel = ...) -> str: ...
    def resolve_path(self, path: str, app: App | Sentinel = ...) -> Any | None: ...
    def after(self, func: _AfterF) -> _AfterF: ...
    def clear_after(self) -> None: ...

class Response(BaseResponse): ...
