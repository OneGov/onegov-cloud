from collections.abc import Callable
from typing import NewType, TypeVar
from typing_extensions import ParamSpec

_T = TypeVar('_T')
_P = ParamSpec('_P')
_DontUse = NewType('_DontUse', object)

# for simplicity we disallow passing in a custom observer
def observes(*paths: str, **observer_kw: _DontUse) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]: ...
