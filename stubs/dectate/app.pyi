from _typeshed import Incomplete
from collections.abc import Generator
from typing import Any

class Config:
    def __getattr__(self, name: str) -> Any: ...

class AppMeta(type):
    def __new__(cls, name, bases, d): ...

class App(metaclass=AppMeta):
    logger_name: str
    dectate: Incomplete
    config: Incomplete
    @classmethod
    def get_directive_methods(cls) -> Generator[Incomplete, None, None]: ...
    @classmethod
    def commit(cls): ...
    @classmethod
    def is_committed(cls): ...
    @classmethod
    def clean(cls) -> None: ...

def directive(action_factory): ...
