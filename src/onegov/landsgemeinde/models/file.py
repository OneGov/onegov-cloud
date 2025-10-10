from __future__ import annotations

from onegov.file.models.file import File
from onegov.file.models.file import SearchableFile


class LandsgemeindeFile(File, SearchableFile):
    """ An attachment to an assembly or agenda item. """

    __mapper_args__ = {'polymorphic_identity': 'landsgemeinde'}

    fts_public = True
