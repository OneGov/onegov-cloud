from __future__ import annotations

from onegov.chat import Message
from sqlalchemy.orm import object_session


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.file import File


class FileMessage(Message):
    __mapper_args__ = {
        'polymorphic_identity': 'file'
    }

    @classmethod
    def log_signature(cls, file: File, signee: str) -> None:
        session = object_session(file)
        assert session is not None
        cls.bound_messages(session).add(
            channel_id=file.id,
            owner=signee,
            meta={
                'name': file.name,
                'action': 'signature',
                'action_metadata': file.signature_metadata
            }
        )

    @classmethod
    def log_signed_file_removal(
        cls,
        file: File,
        username: str | None
    ) -> None:
        session = object_session(file)
        assert session is not None
        cls.bound_messages(session).add(
            channel_id=file.id,
            owner=username,
            meta={
                'name': file.name,
                'action': 'signed-file-removal',
                'action_metadata': None
            }
        )
