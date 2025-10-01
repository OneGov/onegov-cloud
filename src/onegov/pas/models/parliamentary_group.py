from __future__ import annotations

from onegov.parliament.models import ParliamentaryGroup
from onegov.search import ORMSearchable


class PASParliamentaryGroup(ParliamentaryGroup, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentary_group',
    }

    es_type_name = 'pas_parliamentary_group'
    es_public = False
    es_properties = {'name': {'type': 'text', 'weight': 'A'}}

    @property
    def es_suggestion(self) -> str:
        return self.name
