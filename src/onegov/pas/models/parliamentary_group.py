from __future__ import annotations

from onegov.org.models import ParliamentaryGroup


class PASParliamentaryGroup(ParliamentaryGroup):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentary_group',
    }

    es_type_name = 'pas_parliamentary_group'
    es_public = False
