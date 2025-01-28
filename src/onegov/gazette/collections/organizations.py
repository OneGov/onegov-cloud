from __future__ import annotations

from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.gazette.models import Organization


class OrganizationCollection(AdjacencyListCollection[Organization]):
    """ Manage a list of organizations.

    The list is ordered manually (through migration and/or backend).

    """

    __listclass__ = Organization

    def get_unique_child_name(
        self,
        name: str,
        parent: Organization | None
    ) -> str:
        """ Returns a unique name by treating the names as unique integers
        and returning the next value.

        """

        highest_number = max(
            (
                int(name)
                for name, in self.session.query(Organization.name)
                if name.isdigit()
            ),
            default=0
        )
        return str(highest_number + 1)
