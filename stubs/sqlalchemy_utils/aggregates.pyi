from _typeshed import Incomplete
from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar

from sqlalchemy import Column
from sqlalchemy.orm import DeclarativeBase, MappedColumn, Session, declared_attr
from sqlalchemy.sql import ColumnElement, Subquery, Update

_T = TypeVar('_T')

class AggregatedAttribute(declared_attr[_T]):
    column: MappedColumn[_T]
    relationship: str
    def __init__(self, fget: Callable[[Any], ColumnElement[_T]], relationship: str, column: MappedColumn[_T], *args: Incomplete, **kwargs: Incomplete) -> None: ...

class AggregatedValue(Generic[_T]):
    class_: type[DeclarativeBase]
    attr: Column[_T]
    path: str
    expr: ColumnElement[_T]
    def __init__(self, class_: type[Any], attr: Column[_T], path: str, expr: Any): ...
    @property
    def aggregate_query(self) -> Subquery: ...
    def update_query(self, objects: Iterable[DeclarativeBase]) -> Update | None: ...

class AggregationManager:
    generator_registry: dict[type[DeclarativeBase], list[AggregatedValue[Any]]]
    def reset(self) -> None: ...
    def register_listeners(self) -> None: ...
    def update_generator_registry(self) -> None: ...
    def construct_aggregate_queries(self, session: Session, ctx: object) -> None: ...

manager: AggregationManager

def aggregated(relationship: str, column: MappedColumn[_T]) -> Callable[[Callable[[Any], ColumnElement[_T]]], AggregatedAttribute[_T]]: ...
