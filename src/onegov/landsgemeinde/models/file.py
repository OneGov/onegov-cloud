from __future__ import annotations

from onegov.file.models.file import File
from onegov.file.models.file import SearchableFile
from onegov.landsgemeinde.i18n import _


class LandsgemeindeFile(File, SearchableFile):
    """ An attachment to an assembly or agenda item. """

    __mapper_args__ = {'polymorphic_identity': 'landsgemeinde'}

    # FIXME: This conflicts with general files, do we use those?
    #        If so we may need/want to disambiguate?
    fts_type_name = _('Files')
    fts_public = True
