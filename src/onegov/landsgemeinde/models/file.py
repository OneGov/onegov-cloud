from __future__ import annotations

from onegov.file.models.file import File
from onegov.file.models.file import SearchableFile
from onegov.landsgemeinde.i18n import _
from sedate import as_datetime
from sedate import standardize_date


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime


class LandsgemeindeFile(File, SearchableFile):
    """ An attachment to an assembly or agenda item. """

    __mapper_args__ = {'polymorphic_identity': 'landsgemeinde'}

    fts_type_title = _('Files')
    fts_public = True

    @property
    def fts_last_change(self) -> datetime | None:
        date = self.meta.get('assembly_date')
        if date is None:
            return None
        return standardize_date(as_datetime(date), 'Europe/Zurich')
