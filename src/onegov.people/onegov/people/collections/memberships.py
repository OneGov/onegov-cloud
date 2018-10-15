from onegov.core.collection import GenericCollection
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
