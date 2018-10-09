from onegov.people.models import Agency
from onegov.core.orm.abstract import AdjacencyListCollection


class AgencyCollection(AdjacencyListCollection):

    __listclass__ = Agency

    @property
    def roots(self):
        """ Returns the root agencies. """

        return self.query().filter(Agency.parent_id.is_(None)).all()
