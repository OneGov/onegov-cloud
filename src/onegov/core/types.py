from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.collection import (
        _M, PKType, _FormThatSupportsGetUsefulData)
    from typing import TypeVar, Union, Protocol, Any, Literal
    from typing_extensions import NotRequired, TypedDict, Self, TypeAlias
    from collections.abc import Collection, Iterable, Iterator, Sequence
    from sqlalchemy import Column
    from sqlalchemy.orm import Query
    from uuid import UUID
    from functools import cached_property

    from onegov.server.types import (
        JSON, JSON_ro, JSONArray, JSONArray_ro, JSONObject, JSONObject_ro)

    JSON
    JSONObject
    JSONArray

    # read only variant of JSON type that is covariant
    JSON_ro
    JSONObject_ro
    JSONArray_ro

    # output for views rendered through Chameleon
    RenderData: TypeAlias = dict[str, Any]

    MessageType: TypeAlias = Literal['success', 'info', 'warning', 'alert']

    class HeaderJsonDict(TypedDict):
        Name: str
        Value: str

    class AttachmentJsonDict(TypedDict):
        Name: str
        Content: str
        ContentType: str

    class EmailJsonDict(TypedDict):
        From: str
        To: str
        TextBody: str
        MessageStream: str
        ReplyTo: NotRequired[str]
        Cc: NotRequired[str]
        Bcc: NotRequired[str]
        Subject: NotRequired[str]
        HtmlBody: NotRequired[str]
        Headers: NotRequired[list[HeaderJsonDict]]
        Attachments: NotRequired[list[AttachmentJsonDict]]

    class FileDict(TypedDict):
        data: str
        filename: str | None
        mimetype: str
        size: int

    class LaxFileDict(TypedDict):
        data: str
        filename: NotRequired[str | None]
        mimetype: NotRequired[str]
        size: NotRequired[int]

    class HasRole(Protocol):
        @property
        def role(self) -> str: ...

    class PaginatedGenericCollection(Protocol[_M]):
        """ Intersection type of GenericCollection and Pagination, as
          implemented by, for example:
          PaginatedAgencyCollection(GenericCollection, Pagination)"""

        # GenericCollection
        @property
        def model_class(self) -> type[_M]:
            ...

        @cached_property
        def primary_key(self) -> Column[str] | Column[UUID] | Column[int]:
            ...

        def query(self) -> Query[_M]:
            ...

        def by_id(self, id: PKType) -> _M | None:
            ...

        def by_ids(self, ids: Collection[PKType]) -> list[_M]:
            ...

        def add(self, **kwargs: Any) -> _M:
            ...

        def add_by_form(
            self,
            form: _FormThatSupportsGetUsefulData,
            properties: Iterable[str] | None = None,
        ) -> _M:
            ...

        def delete(self, item: _M) -> None:
            ...

        # Pagination:
        batch_size: int

        def __eq__(self, other: object) -> bool:
            ...

        def subset(self) -> Query[_M]:
            ...

        @cached_property
        def cached_subset(self) -> Query[_M]:
            ...

        @property
        def page(self) -> int | None:
            ...

        @page.setter
        def page(self, value: int) -> None:
            ...

        @property
        def page_index(self) -> int:
            ...

        def page_by_index(self, index: int) -> 'Self':
            ...

        def transform_batch_query(self, query: 'Query[_M]') -> 'Query[_M]':
            ...

        @cached_property
        def subset_count(self) -> int:
            ...

        @cached_property
        def batch(self) -> tuple[_M, ...]:
            ...

        @property
        def offset(self) -> int:
            ...

        @property
        def pages_count(self) -> int:
            ...

        @property
        def pages(self) -> 'Iterator[Self]':
            ...

        @property
        def previous(self) -> 'Self | None':
            ...

        @property
        def next(self) -> 'Self | None':
            ...

    _T = TypeVar('_T')
    SequenceOrScalar: TypeAlias = Union[Sequence[_T], _T]

    # TEMPORARY: sqlalchemy-stubs does not have good type annotations
    #            for AppenderQuery, so we define our own, we can get
    #            rid of this once we move to SQLAlchemy 2.0
    class AppenderQuery(Query[_T]):
        def __getitem__(self, index: int) -> _T: ...
        def count(self) -> int: ...
        def extend(self, iterator: Iterable[_T]) -> None: ...
        def append(self, item: _T) -> None: ...
        def remove(self, item: _T) -> None: ...
