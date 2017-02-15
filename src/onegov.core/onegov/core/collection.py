import math

from cached_property import cached_property
from sqlalchemy.inspection import inspect


class GenericCollection(object):

    def __init__(self, session):
        self.session = session

    @property
    def model_class(self):
        raise NotImplementedError

    @cached_property
    def primary_key(self):
        return inspect(self.model_class).primary_key[0]

    def query(self):
        return self.session.query(self.model_class)

    def by_id(self, id):
        return self.query().filter(self.primary_key == id).first()

    def add(self, **kwargs):
        item = self.model_class(**kwargs)

        self.session.add(item)
        self.session.flush()

        return item

    def delete(self, item):
        self.session.delete(item)
        self.session.flush()


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

    def transform_batch_query(self, query):
        """ Allows subclasses to transform the given query before it is
        used to retrieve the batch. This is a good place to add additional
        loading that should only apply to the batch (say joining other
        values to the batch which are then not loaded by the whole query).

        """
        return query

    @cached_property
    def subset_count(self):
        """ Returns the total number of elements this pagination represents.

        """

        # the ordering is entirely unnecessary for a count, so remove it
        # to count things faster
        return self.cached_subset.order_by(None).count()

    @cached_property
    def batch(self):
        """ Returns the elements on the current page. """
        query = self.cached_subset.slice(
            self.offset, self.offset + self.batch_size
        )
        return self.transform_batch_query(query).all()

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
