from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from sqlalchemy import Column
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql import Update

_ColumnT = TypeVar('_ColumnT', bound=Column[Any])

class AggregatedValue:
    # FIXME: should be type[DelarativeBase] in SQLAlchemy 2.0
    class_: type[Any]
    attr: Column[Any]
    path: str
    # FIXME: This should be a valid SQLAlchemy expression or generic function
    expr: Any
    def __init__(self, class_: type[Any], attr: Column[Any], path: str, expr: Any): ...
    @property
    def aggregate_query(self) -> Query[Any]: ...
    # FIXME: This should be Iterable[DeclarativeBase] in SQLAlchemy 2.0
    def update_query(self, objects: Iterable[Any]) -> Update | None: ...

class AggregationManager:
    # FIXME: should be type[DelarativeBase] in SQLAlchemy 2.0
    generator_registry: dict[type[Any], list[AggregatedValue]]
    def reset(self) -> None: ...
    def register_listeners(self) -> None: ...
    def update_generator_registry(self) -> None: ...
    def construct_aggregate_queries(self, session: Session, ctx: object) -> None: ...

manager: AggregationManager

# technically it returns AggregatedAttribute, but its __get__ always return the Column
def aggregated(relationship: str, column: _ColumnT) -> Callable[[Callable[[Any], Any]], _ColumnT]: ...
