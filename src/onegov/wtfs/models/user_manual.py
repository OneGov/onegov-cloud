from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.wtfs import WtfsApp


class UserManual:

    def __init__(self, app: 'WtfsApp'):
        self.app = app
        self.filename = 'user_manual.pdf'
        self.content_type = 'application/pdf'

    @property
    def exists(self) -> bool:
        assert self.app.filestorage is not None
        return self.app.filestorage.exists(self.filename)

    @property
    def pdf(self) -> bytes | None:
        if self.exists:
            assert self.app.filestorage is not None
            with self.app.filestorage.open(self.filename, 'rb') as file:
                # FIXME: This is a bug in FS/SubFS
                return file.read()  # type:ignore
        return None

    @pdf.setter
    def pdf(self, value: bytes) -> None:
        assert self.app.filestorage is not None
        with self.app.filestorage.open(self.filename, 'wb') as file:
            # FIXME: This is a bug in FS/SubFS
            file.write(value)  # type:ignore

    @pdf.deleter
    def pdf(self) -> None:
        if self.exists:
            assert self.app.filestorage is not None
            self.app.filestorage.remove(self.filename)

    @property
    def content_length(self) -> int | None:
        if self.exists:
            assert self.app.filestorage is not None
            return self.app.filestorage.getsize(self.filename)
        return None
