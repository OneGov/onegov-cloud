from __future__ import annotations

from datetime import timedelta
from onegov.org.models.parliament import (
    RISCommission,
    RISCommissionCollection,
    RISCommissionMembership,
    RISCommissionMembershipCollection,
    RISParliamentarian,
    RISParliamentarianCollection,
    RISParliamentarianRoleCollection,
    RISParliamentaryGroup,
    RISParliamentaryGroupCollection,
)
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_ris_commission() -> None:
    commission = RISCommission(name='Finance')
    assert commission.fts_suggestion == 'Finance'
    assert commission.fts_last_change is None


def test_ris_commission_membership_active() -> None:
    assert RISCommissionMembership(end=None).active is True
    assert RISCommissionMembership(
        end=utcnow().date() + timedelta(days=1)).active is True
    assert RISCommissionMembership(
        end=utcnow().date() - timedelta(days=1)).active is False


def test_ris_parliamentarian() -> None:
    parliamentarian = RISParliamentarian(first_name='Anna', last_name='Alpha')
    assert parliamentarian.fts_suggestion == ('Anna Alpha', 'Alpha Anna')
    assert parliamentarian.fts_last_change is None
    assert parliamentarian.title == 'Alpha Anna'
    # no roles and no memberships -> not active
    assert parliamentarian.active is False


def test_ris_parliamentary_group() -> None:
    group = RISParliamentaryGroup(name='Group A')
    assert group.fts_suggestion == 'Group A'
    assert group.fts_last_change is None


def test_collection_model_classes(session: Session) -> None:
    assert RISCommissionCollection(session).model_class is RISCommission
    assert RISCommissionMembershipCollection(
        session).model_class is RISCommissionMembership
    assert RISParliamentarianCollection(
        session).model_class is RISParliamentarian
    assert RISParliamentaryGroupCollection(
        session).model_class is RISParliamentaryGroup
    # RISParliamentarianRoleCollection resolves to the RIS role subclass
    assert RISParliamentarianRoleCollection(session).model_class.__name__ == \
        'RISParliamentarianRole'


def test_membership_collection_active_filter(session: Session) -> None:
    # the active filter applies without rows present
    assert RISCommissionMembershipCollection(
        session, active=True).query().count() == 0
    other = RISCommissionMembershipCollection(session).for_filter(active=False)
    assert other.active is False
