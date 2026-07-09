from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import CommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID  # noqa: F401


class CommissionMembershipCollection[MembershipT: CommissionMembership](
    GenericCollection[MembershipT, 'UUID']
):
    pass
