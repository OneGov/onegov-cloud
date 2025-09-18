from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.parliament.models import CommissionMembership


from typing import TypeVar

MembershipT = TypeVar('MembershipT', bound=CommissionMembership)


class CommissionMembershipCollection(GenericCollection[MembershipT]):
    pass
