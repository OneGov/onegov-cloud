from onegov.directory import Directory, DirectoryEntry
from onegov.org.models.extensions import HiddenFromPublicExtension
from onegov.org.models.extensions import CoordinatesExtension


class ExtendedDirectory(Directory, HiddenFromPublicExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'


class ExtendedDirectoryEntry(DirectoryEntry, CoordinatesExtension,
                             HiddenFromPublicExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directory_entries'
