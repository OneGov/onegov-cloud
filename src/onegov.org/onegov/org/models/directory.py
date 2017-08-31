from onegov.directory import Directory, DirectoryEntry
from onegov.org.models.extensions import HiddenFromPublicExtension


class ExtendedDirectory(Directory, HiddenFromPublicExtension):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directories'


class ExtendedDirectoryEntry(DirectoryEntry):
    __mapper_args__ = {'polymorphic_identity': 'extended'}

    es_type_name = 'extended_directory_entries'
