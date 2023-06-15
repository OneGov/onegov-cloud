from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TypeVar, Union
    from typing_extensions import NotRequired, TypedDict

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
