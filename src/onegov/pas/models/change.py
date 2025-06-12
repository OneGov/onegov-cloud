from __future__ import annotations

from onegov.parliament.models import Change


class PASChange(Change):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_change',
    }

    es_type_name = 'pas_change'
