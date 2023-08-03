from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TypeVar, Union
    from typing_extensions import NotRequired, TypedDict

    from onegov.server.types import (
        JSON, JSON_ro, JSONArray, JSONArray_ro, JSONObject, JSONObject_ro)

    JSON
    JSONObject
    JSONArray

    # read only variant of JSON type that is covariant
    JSON_ro
    JSONObject_ro
    JSONArray_ro

    class EmptyDict(TypedDict):
        pass

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

    _T = TypeVar('_T')
    SequenceOrScalar = Union[Sequence[_T], _T]
