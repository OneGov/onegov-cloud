from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any
    from typing_extensions import TypedDict

    class SignatureMetadata(TypedDict):
        old_digest: str
        new_digest: str
        signee: str
        timestamp: str
        request_id: str
        token: str
        token_type: str

    class FileStats(TypedDict):
        pages: int
        words: int

    class SigningServiceConfig(TypedDict):
        name: str
        parameters: dict[str, Any]
