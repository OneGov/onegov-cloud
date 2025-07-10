from __future__ import annotations

from onegov.org.models import Party


class PASParty(Party):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_party',
    }

    es_type_name = 'pas_party'
    es_public = False
