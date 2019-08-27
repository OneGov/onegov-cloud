from onegov.people.models import Agency
from onegov.core.orm.abstract import AdjacencyListCollection


class AgencyCollection(AdjacencyListCollection):

    """ Manages a list of agencies.

    Use it like this::

        from onegov.people import AgencyCollection
        agencies = AgencyCollection(session)

    """

    __listclass__ = Agency
