from onegov.core.collection import GenericCollection
from onegov.core.orm.abstract import MoveDirection, AdjacencyListCollection
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

    def by_id(self, id):
        return super(AgencyMembershipCollection, self).query().filter(
            self.primary_key == id).first()

    def query(self, order_by=None):
        query = super(AgencyMembershipCollection, self).query()
        if not order_by:
            assert False
        else:
            assert hasattr(self.model_class, order_by)
        return query.order_by(getattr(self.model_class, order_by))

    def move(self, subject, target, direction, move_on_col):
        """ Takes the given subject and moves it somewhere in relation to the
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
        :move_on_col:
            Designates the column for which the new order should be evaluated.
            Possible values are `order_within_agency` and
            `order_within_person`.

        """
        assert isinstance(target, self.model_class)
        assert isinstance(subject, self.model_class)
        assert hasattr(subject, move_on_col)
        assert hasattr(target, move_on_col)

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
            setattr(sibling, move_on_col, order)
