from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.gazette.models import Category


class CategoryCollection(AdjacencyListCollection):
    """ Manage a list of categories. """

    __listclass__ = Category

    def get_unique_child_name(self, name, parent):
        """ Returns a unique name by treating the names as unique integers
        and returning the next value.

        """

        names = sorted([
            int(result[0]) for result in self.session.query(Category.name)
            if result[0].isdigit()
        ])
        next = (names[-1] + 1) if names else 1
        return str(next)

    # todo: add helper to check if this category is used

    # todo: add a helper to update a specific category?
