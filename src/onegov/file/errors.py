from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.file import File


class AlreadySignedError(RuntimeError):
    def __init__(self, file: File):
        super().__init__(f'File {file.id} has already been signed')


class InvalidTokenError(RuntimeError):
    def __init__(self, token: str):
        super().__init__(f'The given token could not be validated: {token}')


class TokenConfigurationError(RuntimeError):
    def __init__(self, token_type: str):
        super().__init__(f'Bad configuration of token type: {token_type}')
