""" Contains the legacy models of files for url redirect support. Going
forward, onegov.file and onegov.org.models.file is used.

"""
from __future__ import annotations

import base64

from onegov.core.filestorage import FilestorageFile
from onegov.core import utils


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date as date_t
    from onegov.org.app import OrgApp
    from typing import Self


class LegacyFileCollection:

    def __init__(self, app: OrgApp) -> None:
        assert app.has_filestorage and app.filestorage is not None

        self.path_prefix = 'files/'
        self.file_storage = utils.makeopendir(app.filestorage, 'files')

    def get_file_by_filename(self, filename: str) -> LegacyFile | None:
        if self.file_storage.exists(filename):
            return LegacyFile(filename)
        return None


class LegacyImageCollection:

    def __init__(self, app: OrgApp) -> None:
        assert app.has_filestorage and app.filestorage is not None

        self.path_prefix = 'images/'
        self.file_storage = utils.makeopendir(app.filestorage, 'images')

    def get_file_by_filename(self, filename: str) -> LegacyImage | None:
        if self.file_storage.exists(filename):
            return LegacyImage(filename)
        return None


class LegacyFile(FilestorageFile):
    """ A filestorage file that points to an uploaded image or file. """

    def __init__(self, filename: str, info: dict[str, Any] | None = None):
        self.filename = filename
        self.info = info or {}

    @property
    def date(self) -> date_t | None:
        if 'modified_time' in self.info:
            return self.info['modified_time'].date()
        return None

    @property
    def path(self) -> str:  # type:ignore[override]
        return 'files/' + self.filename

    @property
    def original_name(self) -> bytes | None:
        if '-' in self.filename:
            name = str(self.filename.split('-')[0])
            return base64.urlsafe_b64decode(name).strip()
        return None

    @classmethod
    def from_url(cls, url: str) -> Self:
        return cls(url.split('/')[-1])


class LegacyImage(LegacyFile):
    """ A filestorage file that points to a full image (not a thumbnail). """

    @property
    def path(self) -> str:  # type:ignore[override]
        return 'images/' + self.filename
