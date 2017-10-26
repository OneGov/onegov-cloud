from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.gazette.models import Organization


class OrganizationCollection(AdjacencyListCollection):
    """ Manage a list of organizations.

    The list is ordered manually (through migration and/or backend).

    """

    __listclass__ = Organization

    def get_unique_child_name(self, name, parent):
        """ Returns a unique name by treating the names as unique integers
        and returning the next value.

        """

        names = sorted([
            int(result[0]) for result in self.session.query(Organization.name)
            if result[0].isdigit()
        ])
        next = (names[-1] + 1) if names else 1
        return str(next)
