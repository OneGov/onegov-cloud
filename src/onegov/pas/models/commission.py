from __future__ import annotations

from onegov.parliament.models import Commission


class PASCommission(Commission):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_commission',
    }

    es_type_name = 'pas_commission'
