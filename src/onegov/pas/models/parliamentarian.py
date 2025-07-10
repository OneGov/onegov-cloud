from __future__ import annotations

from onegov.org.models import Parliamentarian


class PASParliamentarian(Parliamentarian):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentarian',
    }

    es_type_name = 'pas_parliamentarian'
    es_public = False
