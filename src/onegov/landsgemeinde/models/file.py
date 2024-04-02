from onegov.file.models.file import File
from onegov.file.models.file import SearchableFile


class LandsgemeindeFile(File, SearchableFile):
    """ An attachment to an assembly or agenda item. """

    __mapper_args__ = {'polymorphic_identity': 'landsgemeinde'}

    es_type_name = 'landsgemeinde_file'

    @property
    def es_public(self) -> bool:
        return True
