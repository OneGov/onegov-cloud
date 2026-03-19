from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import CommissionMembership


class CommissionMembershipCollection[MembershipT: CommissionMembership](
    GenericCollection[MembershipT]
):
    pass
