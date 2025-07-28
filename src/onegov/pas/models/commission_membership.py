from __future__ import annotations

from onegov.parliament.models import CommissionMembership


class PASCommissionMembership(CommissionMembership):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_commission_membership',
    }
