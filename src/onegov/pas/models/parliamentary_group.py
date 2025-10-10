from __future__ import annotations

from onegov.parliament.models import ParliamentaryGroup
from onegov.search import ORMSearchable


class PASParliamentaryGroup(ParliamentaryGroup, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentary_group',
    }

    fts_public = False
    fts_properties = {'name': {'type': 'text', 'weight': 'A'}}

    @property
    def fts_suggestion(self) -> str:
        return self.name
