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

    def add_by_form(self, form, properties=None):
        cls = self.model_class

        return self.add(**{
            # fields
            k: v for k, v in form.get_useful_data().items() if hasattr(cls, k)
        }, **{
            # attributes
            k: getattr(form, k) for k in properties or tuple()
        })

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
        return tuple(self.transform_batch_query(query))

    @property
    def offset(self):
        """ Returns the offset applied to the current subset. """
        return self.page * self.batch_size

    @property
    def pages_count(self):
        """ Returns the number of pages. """
        if not self.batch_size:
            return 1
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


class RangedPagination(object):
    """ Provides a pagination that supports loading multiple pages at once.

    This is useful in a context where a single button is used to 'load more'
    results one by one. In this case we need an URL that represents what's
    happening on the screen (multiple pages are shown at the same time).

    """

    # how many items are shown per page
    batch_size = 10

    # how many items may be shown together, ranges exceeding this limit are
    # may be clipped by using `limit_range`.
    range_limit = 5

    def subset(self):
        """ Returns an SQLAlchemy query containing all records that should
        be considered for pagination.

        """
        raise NotImplementedError

    @cached_property
    def cached_subset(self):
        return self.subset()

    @property
    def page_range(self):
        """ Returns the current page range (starting at (0, 0)). """
        raise NotImplementedError

    def by_page_range(self, page_range):
        """ Returns an instance of the collection limited to the given
        page range.

        """

        raise NotImplementedError

    def limit_range(self, page_range, direction):
        """ Limits the range to the range limit in the given direction.

        For example, 0-99 will be limited to 89-99 with a limit of 10 and 'up'.
        With 'down' it will be limited to 0-9.

        """
        assert direction in ('up', 'down')
        s, e = page_range

        if e < s:
            s, e = e, s

        if (e - s) > self.range_limit:
            if direction == 'down':
                return s, s + self.range_limit
            else:
                return max(0, e - self.range_limit), e

        return (s, e)

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
        """ Returns the elements on the current page range. """
        s, e = self.page_range

        s = s * self.batch_size
        e = e * self.batch_size + self.batch_size

        query = self.cached_subset.slice(s, e)

        return tuple(self.transform_batch_query(query))

    @property
    def pages_count(self):
        """ Returns the number of pages. """
        if not self.batch_size:
            return 1

        return int(math.ceil(self.subset_count / self.batch_size))

    @property
    def previous(self):
        """ Returns the previous page or None. """
        s, e = self.page_range

        if s > 0:
            return self.by_page_range((s - 1, s - 1))

    @property
    def next(self):
        """ Returns the next page range or None. """
        s, e = self.page_range

        if e + 1 < self.pages_count:
            return self.by_page_range((e + 1, e + 1))
