from __future__ import annotations

from onegov.org.models import LegislativePeriod


class PASLegislativePeriod(LegislativePeriod):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_legislative_period',
    }

    es_type_name = 'pas_legislative_period'
    es_public = False
