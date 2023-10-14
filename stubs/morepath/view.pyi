from collections.abc import Callable
from typing import Any, TypeVar, overload

from dectate.config import CodeInfo
from morepath.app import App
from morepath.request import Request, Response
from webob import Response as BaseResponse
from webob.exc import HTTPFound

_T = TypeVar('_T')
_L = TypeVar('_L')
_RequestT = TypeVar('_RequestT', bound=Request, contravariant=True)

class View:
    func: Callable[..., Any]
    render: Callable[[Any], BaseResponse] | None
    load: Callable[[_RequestT], Any] | None
    permission: Any | None
    internal: bool
    code_info: CodeInfo | None
    @overload
    def __init__(
        self,
        # we are lax and allow views that depend on subclasses of Request
        func: Callable[[Any, _RequestT], BaseResponse],
        render: None = None,
        load: None = None,
        permission: object | None = None,
        internal: bool = False,
        code_info: CodeInfo | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        func: Callable[[Any, _RequestT], _T],
        render: Callable[[_T], BaseResponse],
        load: None = None,
        permission: object | None = None,
        internal: bool = False,
        code_info: CodeInfo | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        func: Callable[[Any, _RequestT, _L], _T],
        render: Callable[[_T], BaseResponse],
        load: Callable[[], _L],
        permission: object | None = None,
        internal: bool = False,
        code_info: CodeInfo | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        func: Callable[[Any, _RequestT, _L], BaseResponse],
        render: None,
        load: Callable[[], _L],
        permission: object | None = None,
        internal: bool = False,
        code_info: CodeInfo | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        func: Callable[[Any, _RequestT, _L], BaseResponse],
        render: None = None,
        *,
        load: Callable[[], _L],
        permission: object | None = None,
        internal: bool = False,
        code_info: CodeInfo | None = None,
    ) -> None: ...
    def __call__(self, app: App, obj: object, request: Request) -> BaseResponse: ...

def render_view(content: str, request: Request) -> Response: ...
def render_json(content: Any, request: Request) -> Response: ...
def render_html(content: str, request: Request) -> Response: ...
def redirect(location: str) -> HTTPFound: ...
