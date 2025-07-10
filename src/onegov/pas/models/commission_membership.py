from __future__ import annotations

from onegov.org.models import CommissionMembership


class PASCommissionMembership(CommissionMembership):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_commission_membership',
    }

    es_type_name = 'pas_commission_membership'
