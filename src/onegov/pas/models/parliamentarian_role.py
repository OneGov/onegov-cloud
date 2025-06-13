from __future__ import annotations

from onegov.parliament.models import ParliamentarianRole


class PASParliamentarianRole(ParliamentarianRole):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentarian_role',
    }

    es_type_name = 'pas_parliamentarian_role'
