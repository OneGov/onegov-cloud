from onegov.core.orm.abstract import AdjacencyListCollection
from onegov.page.model import Page


class PageCollection(AdjacencyListCollection):
    """ Manages a hierarchy of pages.

    Use it like this:

        from onegov.page import PageCollection
        pages = PageCollection(session)

    """

    __listclass__ = Page

    def copy(self, page, parent):
        """ Takes the given page and copies it to a given parent.

        The parent may be the same as the given page or another. If there's
        a conflict with existing children, the name is adjusted using
        :meth:`get_unique_child_name`.

        """
        return self.add(
            parent=parent,
            title=page.title,
            type=page.type,
            meta=page.meta,
            content=page.content
        )
