from collections.abc import Callable
from typing import overload, Generic, TypeVar
from typing_extensions import Self

from dectate import commit as commit

from .app import App as App, dispatch_method as dispatch_method
from .authentication import NO_IDENTITY as NO_IDENTITY, Identity as Identity, IdentityPolicy as IdentityPolicy
from .autosetup import autoscan as autoscan, scan as scan
from .converter import Converter as Converter
# from .core import (
#     model_predicate as model_predicate,
#     name_predicate as name_predicate,
#     request_method_predicate as request_method_predicate,
# )
from .request import Request as Request, Response as Response
# from .run import run as run
from .view import redirect as redirect, render_html as render_html, render_json as render_json

_T = TypeVar('_T')
_RT = TypeVar('_RT')

# this is technically defined in a module, but since the module is called the
# same as the class and the class gets imported into the global module, mypy
# will get confused and shadow the class with the module or vice versa, so
# it is easier to just define the class here
class reify(Generic[_T, _RT]):
    wrapped: Callable[[_T], _RT]
    def __init__(self: reify[_T, _RT], wrapped: Callable[[_T], _RT]) -> None: ...
    @overload
    def __get__(self, inst: None, objtype: type[_T] | None = None) -> Self: ...
    @overload
    def __get__(self, inst: _T, objtype: type[_T] | None = None) -> _RT: ...
