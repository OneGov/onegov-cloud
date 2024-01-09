from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.gazette.models import Category


class CategoryCollection(AdjacencyListCollection[Category]):
    """ Manage a list of categories.

    The list is ordered by the title, unless the ordering is set manually
    (which should never occure in our case).

    """

    __listclass__ = Category

    def get_unique_child_name(self, name: str, parent: Category | None) -> str:
        """ Returns a unique name by treating the names as unique integers
        and returning the next value.

        """

        highest_number = max(
            (
                int(name)
                for name, in self.session.query(Category.name)
                if name.isdigit()
            ),
            default=0
        )
        return str(highest_number + 1)
