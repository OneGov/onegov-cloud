from __future__ import annotations

from functools import cached_property
from onegov.people import AgencyMembershipCollection


from typing import Generic
from typing import Protocol
from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.collections import ExtendedAgencyCollection
    from onegov.agency.models import ExtendedAgency  # noqa: F401
    from onegov.core.orm import Base
    from onegov.core.orm.abstract import MoveDirection
    from onegov.people import AgencyMembership  # noqa: F401
    from sqlalchemy.orm import Session
    from uuid import UUID


_M = TypeVar('_M', bound='Base')
_M_co = TypeVar('_M_co', bound='Base', covariant=True)
_IdT_contra = TypeVar('_IdT_contra', bound='UUID | int', contravariant=True)


class SupportsById(Protocol[_M_co, _IdT_contra]):
    def by_id(self, id: _IdT_contra, /) -> _M_co | None: ...


class Move(Generic[_M, _IdT_contra]):
    """ Base class for moving things. """

    def __init__(
        self,
        session: Session,
        subject_id: _IdT_contra,
        target_id: _IdT_contra,
        direction: MoveDirection
    ) -> None:
        self.session = session
        self.subject_id = subject_id
        self.target_id = target_id
        self.direction = direction

    @cached_property
    def collection(self) -> SupportsById[_M, _IdT_contra]:
        raise NotImplementedError

    @cached_property
    def subject(self) -> _M | None:
        return self.collection.by_id(self.subject_id)

    @cached_property
    def target(self) -> _M | None:
        return self.collection.by_id(self.target_id)

    def execute(self) -> None:
        raise NotImplementedError


class AgencyMove(Move['ExtendedAgency', int]):
    """ Represents a single move of a suborganization. """

    @cached_property
    def collection(self) -> ExtendedAgencyCollection:
        from onegov.agency.collections import ExtendedAgencyCollection
        return ExtendedAgencyCollection(self.session)

    def execute(self) -> None:
        if self.subject and self.target and self.subject != self.target:
            if self.subject.parent_id == self.target.parent_id:
                self.collection.move(
                    subject=self.subject,
                    target=self.target,
                    direction=self.direction
                )


class AgencyMembershipMoveWithinAgency(Move['AgencyMembership', 'UUID']):
    """ Represents a single move of a membership with respect to a Agency. """

    @cached_property
    def collection(self) -> AgencyMembershipCollection:
        return AgencyMembershipCollection(self.session)

    def execute(self) -> None:
        if self.subject and self.target and self.subject != self.target:
            if self.subject.agency_id == self.target.agency_id:
                self.collection.move(
                    subject=self.subject,
                    target=self.target,
                    direction=self.direction,
                    move_on_col='order_within_agency'
                )


class AgencyMembershipMoveWithinPerson(Move['AgencyMembership', 'UUID']):
    """ Represents a single move of a membership with respect to a Person. """

    @cached_property
    def collection(self) -> AgencyMembershipCollection:
        return AgencyMembershipCollection(self.session)

    def execute(self) -> None:
        if self.subject and self.target and self.subject != self.target:
            if self.subject.person_id == self.target.person_id:
                self.collection.move(
                    subject=self.subject,
                    target=self.target,
                    direction=self.direction,
                    move_on_col='order_within_person'
                )
