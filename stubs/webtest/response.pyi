import re
from _typeshed.wsgi import WSGIApplication
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal, Self, TypeAlias, TypedDict, Unpack, overload
from xml.etree import ElementTree

from bs4 import BeautifulSoup
from lxml.etree import _Element
from pyquery import PyQuery  # type: ignore
from webob import Response
from webtest.app import _Files, TestApp, TestRequest
from webtest.forms import Form

_Pattern: TypeAlias = str | bytes | re.Pattern[str] | Callable[[str], bool]

class _GetParams(TypedDict, total=False):
    params: Mapping[str, str] | str
    headers: Mapping[str, str]
    extra_environ: Mapping[str, Any]
    status: int | str | None
    expect_errors: bool
    xhr: bool

class _PostParams(_GetParams, total=False):
    upload_files: _Files
    content_type: str

class TestResponse(Response):
    request: TestRequest  # type: ignore[assignment]
    app: WSGIApplication
    test_app: TestApp[Any]
    parser_features: str
    __test__: Literal[False]
    @property
    def forms(self) -> dict[str | int, Form]: ...
    @property
    def form(self) -> Form: ...
    @property
    def testbody(self) -> str: ...
    def follow(self, **kw: Unpack[_GetParams]) -> Self: ...
    def maybe_follow(self, **kw: Unpack[_GetParams]) -> Self: ...
    def click(
        self,
        description: _Pattern | None = None,
        linkid: _Pattern | None = None,
        href: _Pattern | None = None,
        index: int | None = None,
        verbose: bool = False,
        extra_environ: dict[str, Any] | None = None,
    ) -> Self: ...
    def clickbutton(
        self,
        description: _Pattern | None = None,
        buttonid: _Pattern | None = None,
        href: _Pattern | None = None,
        onclick: str | None = None,
        index: int | None = None,
        verbose: bool = False,
    ) -> Self: ...
    @overload
    def goto(self, href: str, method: Literal["get"] = "get", **args: Unpack[_GetParams]) -> Self: ...
    @overload
    def goto(self, href: str, method: Literal["post"], **args: Unpack[_PostParams]) -> Self: ...
    @property
    def normal_body(self) -> bytes: ...
    @property
    def unicode_normal_body(self) -> str: ...
    def __contains__(self, s: str) -> bool: ...
    def mustcontain(self, *strings: str, no: Sequence[str] | str = ...) -> None: ...
    @property
    def html(self) -> BeautifulSoup: ...
    @property
    def xml(self) -> ElementTree.Element: ...
    @property
    def lxml(self) -> _Element: ...
    @property
    def json(self) -> Any: ...
    @property
    def pyquery(self) -> PyQuery: ...
    def PyQuery(self, **kwargs: Any) -> PyQuery: ...
    def showbrowser(self) -> None: ...
    def __str__(self) -> str: ...  # type: ignore[override]  # noqa: PYI029
