import inspect
import importlib

from typing import overload, Any, TypeVar

_T = TypeVar('_T')


@overload
def load_class(cls: type[_T]) -> type[_T]: ...
@overload
def load_class(cls: str) -> type[Any] | None: ...


def load_class(cls: type[Any] | str) -> type[Any] | None:
    """ Loads the given class from string (unless alrady a class). """

    if inspect.isclass(cls):
        return cls

    module_name, _, class_name = cls.rpartition('.')
    module = importlib.import_module(module_name)

    # FIXME: Why are we supplying a default return, when import_module
    #        already could fail? It seems better to always raise an
    #        exception when the class doesn't exist... It might also be
    #        worth to use __import__ so we get the same error we would
    #        get if we tried to do `from module_name import class_name`
    return getattr(module, class_name, None)
