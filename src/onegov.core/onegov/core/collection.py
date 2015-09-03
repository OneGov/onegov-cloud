from __future__ import division

import math

from cached_property import cached_property


class Pagination(object):
    """ Provides collections with pagination, if they implement a few
    documented properties and methods.

    See :class:`onegov.ticket.TicketCollection` for an example.

    """

    batch_size = 10

    def __eq__(self, other):
        """ Returns True if the current and the other Pagination instance
        are equal. Used to find the current page in a list of pages.

        """
        raise NotImplementedError

    def subset(self):
        """ Returns an SQLAlchemy query containing all records that should
        be considered for pagination.

        """
        raise NotImplementedError

    @cached_property
    def cached_subset(self):
        return self.subset()

    @property
    def page_index(self):
        """ Returns the current page index (starting at 0). """
        raise NotImplementedError

    def page_by_index(self, index):
        """ Returns the page at the given index. A page here means an instance
        of the class inheriting from the ``Pagination`` base class.

        """
        raise NotImplementedError

    @cached_property
    def subset_count(self):
        """ Returns the total number of elements this pagination represents.

        """
        return self.cached_subset.count()

    @cached_property
    def batch(self):
        """ Returns the elements on the current page. """
        query = self.cached_subset.slice(
            self.offset, self.offset + self.batch_size
        )
        return query.all()

    @property
    def offset(self):
        """ Returns the offset applied to the current subset. """
        return self.page * self.batch_size

    @property
    def pages_count(self):
        """ Returns the number of pages. """
        return int(math.ceil(self.subset_count / self.batch_size))

    @property
    def pages(self):
        """ Yields all page objects of this Pagination. """
        for page in range(0, self.pages_count):
            yield self.page_by_index(page)

    @property
    def previous(self):
        """ Returns the previous page or None. """
        if self.page - 1 >= 0:
            return self.page_by_index(self.page - 1)

    @property
    def next(self):
        """ Returns the next page or None. """
        if self.page + 1 < self.pages_count:
            return self.page_by_index(self.page + 1)
