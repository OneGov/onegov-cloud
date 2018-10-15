from onegov.people.models import Agency
from onegov.core.orm.abstract import AdjacencyListCollection


class AgencyCollection(AdjacencyListCollection):

    """ Manages a list of agencies.

    Use it like this::

        from onegov.people import AgencyCollection
        agencies = AgencyCollection(session)

    """

    __listclass__ = Agency

    @property
    def roots(self):
        """ Returns the root agencies. """

        return self.query().filter(
            self.__listclass__.parent_id.is_(None)
        ).all()
