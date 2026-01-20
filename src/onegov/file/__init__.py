from __future__ import annotations

import logging
log = logging.getLogger('onegov.file')
log.addHandler(logging.NullHandler())

from onegov.file.collection import FileCollection, FileSetCollection
from onegov.file.integration import DepotApp
from onegov.file.models import (
    AssociatedFiles,
    File,
    FileSet,
    MultiAssociatedFiles,
    NamedFile,
    SearchableFile
)

__all__ = (
    'log',
    'AssociatedFiles',
    'DepotApp',
    'File',
    'FileCollection',
    'FileSet',
    'FileSetCollection',
    'MultiAssociatedFiles',
    'NamedFile',
    'SearchableFile'
)
