from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import (
        Any, Literal, NotRequired, Protocol, TypedDict, TypeAlias, TypeVar)

    # re-export JSON types
    from onegov.server.types import (
        JSON as JSON,
        JSON_ro as JSON_ro,
        JSONArray as JSONArray,
        JSONArray_ro as JSONArray_ro,
        JSONObject as JSONObject,
        JSONObject_ro as JSONObject_ro
    )

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
