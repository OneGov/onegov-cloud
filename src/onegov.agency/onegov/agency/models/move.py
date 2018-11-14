from onegov.core.orm.abstract import MoveDirection


class Move(object):
    """ Base class for moving things. """

    def __init__(self, session, subject_id, target_id, direction):
        self.session = session
        self.subject_id = subject_id
        self.target_id = target_id
        self.direction = direction

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

    def execute(self):
        from onegov.agency.collections import ExtendedAgencyCollection

        agencies = ExtendedAgencyCollection(self.session)
        subject = agencies.by_id(self.subject_id)
        target = agencies.by_id(self.target_id)
        if subject and target and subject != target:
            if subject.parent_id == target.parent_id:
                agencies.move(
                    subject=subject,
                    target=target,
                    direction=getattr(MoveDirection, self.direction)
                )


class AgencyMembershipMove(Move):
    """ Represents a single move of a membership. """

    def execute(self):
        from onegov.people import AgencyMembershipCollection

        memberships = AgencyMembershipCollection(self.session)
        subject = memberships.by_id(self.subject_id)
        target = memberships.by_id(self.target_id)
        if subject and target and subject != target:
            if subject.agency_id == target.agency_id:
                memberships.move(
                    subject=subject,
                    target=target,
                    direction=getattr(MoveDirection, self.direction)
                )
