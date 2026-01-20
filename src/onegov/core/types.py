from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import (
        Any, Literal, NotRequired, Protocol, TypedDict, TypeAlias, TypeVar)
    from collections.abc import Iterable, Sequence
    from sqlalchemy.orm import Query

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

    _T = TypeVar('_T')
    SequenceOrScalar: TypeAlias = Sequence[_T] | _T

    # TEMPORARY: sqlalchemy-stubs does not have good type annotations
    #            for AppenderQuery, so we define our own, we can get
    #            rid of this once we move to SQLAlchemy 2.0
    class AppenderQuery(Query[_T]):
        def __getitem__(self, index: int) -> _T: ...
        # NOTE: Avoids comparison-overlap errors
        def __eq__(self, other: object) -> bool: ...
        def count(self) -> int: ...
        def extend(self, iterator: Iterable[_T]) -> None: ...
        def append(self, item: _T) -> None: ...
        def remove(self, item: _T) -> None: ...
