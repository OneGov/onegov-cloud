from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import TypeVar, Union
    from typing_extensions import NotRequired, TypedDict

    JSON = (
        dict[str, 'JSON'] | list['JSON']
        | str | int | float | bool | None
    )
    JSONObject = dict[str, JSON]
    JSONArray = list[JSON]

    # read only variant of JSON type that is covariant
    JSON_ro = (
        Mapping[str, 'JSON_ro'] | Sequence['JSON_ro']
        | str | int | float | bool | None
    )
    JSONObject_ro = Mapping[str, JSON_ro]
    JSONArray_ro = Sequence[JSON_ro]

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

    _T = TypeVar('_T')
    SequenceOrScalar = Union[Sequence[_T], _T]
