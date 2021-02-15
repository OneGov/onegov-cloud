from cached_property import cached_property
from onegov.core.orm.abstract import MoveDirection


class Move(object):
    """ Base class for moving things. """

    def __init__(self, session, subject_id, target_id, direction):
        self.session = session
        self.subject_id = subject_id
        self.target_id = target_id
        self.direction = direction

    @cached_property
    def collection(self):
        raise NotImplementedError

    @cached_property
    def subject(self):
        return self.collection.by_id(self.subject_id)

    @cached_property
    def target(self):
        return self.collection.by_id(self.target_id)

    @classmethod
    def for_url_template(cls):
        return cls(
            session=None,
            subject_id='{subject_id}',
            target_id='{target_id}',
            direction='{direction}'
        )

    def execute(self):
        raise NotImplementedError


class AgencyMove(Move):
    """ Represents a single move of a suborganization. """

    @cached_property
    def collection(self):
        from onegov.agency.collections import ExtendedAgencyCollection
        return ExtendedAgencyCollection(self.session)

    def execute(self):
        if self.subject and self.target and self.subject != self.target:
            if self.subject.parent_id == self.target.parent_id:
                self.collection.move(
                    subject=self.subject,
                    target=self.target,
                    direction=getattr(MoveDirection, self.direction)
                )


class AgencyMembershipMoveWithinAgency(Move):
    """ Represents a single move of a membership with respect to a Agency. """

    @cached_property
    def collection(self):
        from onegov.people import AgencyMembershipCollection
        return AgencyMembershipCollection(self.session)

    def execute(self):
        if self.subject and self.target and self.subject != self.target:
            if self.subject.agency_id == self.target.agency_id:
                self.collection.move(
                    subject=self.subject,
                    target=self.target,
                    direction=getattr(MoveDirection, self.direction),
                    move_on_col='order_within_agency'
                )


class AgencyMembershipMoveWithinPerson(Move):
    """ Represents a single move of a membership with respect to a Person. """

    @cached_property
    def collection(self):
        from onegov.people import AgencyMembershipCollection
        return AgencyMembershipCollection(self.session)

    def execute(self):
        if self.subject and self.target and self.subject != self.target:
            if self.subject.person_id == self.target.person_id:
                self.collection.move(
                    subject=self.subject,
                    target=self.target,
                    direction=getattr(MoveDirection, self.direction),
                    move_on_col='order_within_person'
                )
