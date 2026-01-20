from __future__ import annotations

from onegov.parliament.models import ParliamentaryGroup
from onegov.pas.i18n import _
from onegov.search import ORMSearchable


class PASParliamentaryGroup(ParliamentaryGroup, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentary_group',
    }

    fts_type_title = _('Parliamentary groups')
    fts_public = False
    fts_title_property = 'name'
    fts_properties = {'name': {'type': 'text', 'weight': 'A'}}

    @property
    def fts_suggestion(self) -> str:
        return self.name
