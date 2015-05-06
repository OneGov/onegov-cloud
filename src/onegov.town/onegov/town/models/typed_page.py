import morepath

from cached_property import cached_property
from lazy_object_proxy import Proxy


class TypedPage(Proxy):
    """ Wraps the :class:`onegov.page.model.Page`, adding type information.

    To wrap an existing page instance use :meth:`from_page`.

    """

    def __init__(self, wrapped):
        super(TypedPage, self).__init__(lambda: wrapped)

    @staticmethod
    def from_page(page, acceptable_types=None):
        """ Returns a wrapped page or None.

        :acceptable_types:
            A list of types that are acceptable. If the given page does not
            have any of those types, None is returned.

        """

        if page is None:
            return None

        page_type = page.meta.get('type')

        if acceptable_types is None or page_type in acceptable_types:
            return TypedPage(page)
        else:
            return None

    @property
    def type(self):
        """ Returns the type of the page. """
        return self.meta.get('type')

    @cached_property
    def type_info_map(self):
        """ Returns type info of all page types. """
        return morepath.settings().pages.type_info

    @cached_property
    def type_info(self):
        """ Returns type info of the current page. """
        return morepath.settings().pages.type_info[self.type]
