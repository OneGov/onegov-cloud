from onegov.file.collection import FileCollection, FileSetCollection
from onegov.file.integration import DepotApp
from onegov.file.models import File, FileSet

from onegov.file import hotfix  # noqa

__all__ = [
    'DepotApp',
    'File',
    'FileCollection',
    'FileSet',
    'FileSetCollection'
]
