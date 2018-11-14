from onegov.core.collection import GenericCollection
from onegov.core.orm.abstract import MoveDirection
from onegov.people.models import AgencyMembership


class AgencyMembershipCollection(GenericCollection):
    """ Manages a list of agency memberships.

    Use it like this::

        from onegov.people import AgencyMembershipCollection
        memberships = AgencyMembershipCollection(session)

    """

    @property
    def model_class(self):
        return AgencyMembership

    def query(self):
        query = super(AgencyMembershipCollection, self).query()
        return query.order_by(self.model_class.order)

    def move(self, subject, target, direction):
        """ Takes the given subject and moves it somehwere in relation to the
        target.

        :subject:
            The item to be moved.

        :target:
            The item above which or below which the subject is moved.

        :direction:
            The direction relative to the target. Either
            :attr:`MoveDirection.above` if the subject should be moved
            above the target, or :attr:`MoveDirection.below` if the subject
            should be moved below the target.

        """
        assert direction in MoveDirection
        assert subject != target
        assert target.agency_id == subject.agency_id

        siblings = target.siblings.all()

        def new_order():
            for sibling in siblings:
                if sibling == subject:
                    continue

                if sibling == target and direction == MoveDirection.above:
                    yield subject
                    yield target
                    continue

                if sibling == target and direction == MoveDirection.below:
                    yield target
                    yield subject
                    continue

                yield sibling

        for order, sibling in enumerate(new_order()):
            sibling.order = order
