from __future__ import annotations

import math

from functools import cached_property
from sqlalchemy import func, or_
from sqlalchemy.inspection import inspect


from typing import Any, Generic, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsItems
    from abc import abstractmethod
    from collections.abc import Collection, Iterable, Iterator, Sequence
    from sqlalchemy import ColumnElement
    from sqlalchemy.sql.elements import SQLCoreOperations
    from sqlalchemy.orm import DeclarativeBase, Query, Session
    from typing import Protocol
    from typing import Self
    from uuid import UUID

    # TODO: Maybe PKType should be generic as well? Or if we always
    #       use the same kind of primary key, then we can reduce
    #       this type union to something more specific
    PKType = UUID | str | int
    TextColumn = ColumnElement[str] | ColumnElement[str | None]

    # NOTE: To avoid referencing onegov.form from onegov.core and
    #       introducing a cross-dependency, we use a Protocol to
    #       forward declare exactly the attributes we require to
    #       be implemented for a Form class, so it can be used with
    #       our GenericCollection
    class _FormThatSupportsGetUsefulData(Protocol):
        def get_useful_data(self) -> SupportsItems[str, Any]: ...


_M = TypeVar('_M', bound='DeclarativeBase')


class GenericCollection(Generic[_M]):

    def __init__(self, session: Session, **kwargs: Any):
        self.session = session

    @property
    def model_class(self) -> type[_M]:
        raise NotImplementedError

    @cached_property
    def primary_key(self) -> (
        ColumnElement[str]
        | ColumnElement[UUID]
        | ColumnElement[int]
    ):
        return inspect(self.model_class).primary_key[0]

    def query(self) -> Query[_M]:
        return self.session.query(self.model_class)

    def by_id(self, id: PKType) -> _M | None:
        return self.query().filter(self.primary_key == id).first()

    def by_ids(self, ids: Collection[PKType]) -> list[_M]:
        return self.query().filter(
            self.primary_key.in_(ids)
        ).all() if ids else []

    # NOTE: Subclasses should be more specific, so we get type
    #       safety on the constructor of the model, ideally the
    #       subclasses also set kwargs to Never at that point
    #       so we get an error if we use an argument that doesn't
    #       exist for the given model
    def add(self, **kwargs: Any) -> _M:
        item = self.model_class(**kwargs)

        self.session.add(item)
        self.session.flush()

        return item

    def add_by_form(
        self,
        form: _FormThatSupportsGetUsefulData,
        properties: Iterable[str] | None = None
    ) -> _M:

        cls = self.model_class
        return self.add(**{
            # fields
            k: v for k, v in form.get_useful_data().items() if hasattr(cls, k)
        }, **{
            # attributes
            k: getattr(form, k) for k in properties or ()
        })

    def delete(self, item: _M) -> None:
        self.session.delete(item)
        self.session.flush()


class SearcheableCollection(GenericCollection[_M]):

    """
    Requires a self.locale and self.term
    """

    @staticmethod
    def match_term(
        column: SQLCoreOperations[str | None],
        language: str,
        term: str
    ) -> ColumnElement[bool]:
        """
        Usage:
        model.filter(match_term(model.col, 'german', 'my search term'))

        """
        document_tsvector = func.to_tsvector(language, column)
        ts_query_object = func.to_tsquery(language, term)
        return document_tsvector.op('@@')(ts_query_object)

    @staticmethod
    def term_to_tsquery_string(term: str) -> str:
        """ Returns the current search term transformed to use within
        Postgres ``to_tsquery`` function.
        Removes all unwanted characters, replaces prefix matching, joins
        word together using FOLLOWED BY.
        """

        def cleanup(word: str, whitelist_chars: str = ',.-_') -> str:
            # FIXME: str.translate or even re.sub might be faster
            result = ''.join(
                char
                for char in word
                if char.isalnum() or char in whitelist_chars
            )
            return f'{result}:*' if word.endswith('*') else result

        parts = (cleanup(part) for part in (term or '').split())
        return ' <-> '.join(tuple(part for part in parts if part))

    def filter_text_by_locale(
        self,
        column: SQLCoreOperations[str | None],
        term: str,
        locale: str | None = None
    ) -> ColumnElement[bool]:
        """
        Returns an SqlAlchemy filter statement based on the search term.
        If no locale is provided, it will use english as language.

        ``to_tsquery`` creates a tsquery value from term,
        which must consist of single tokens separated by the Boolean operators
        & (AND), | (OR) and ! (NOT).

        ``to_tsvector`` parses a textual document into tokens, reduces the
        tokens to lexemes, and returns a tsvector which lists the lexemes
        together with their positions in the document. The document is
        processed according to the specified or default text search
        configuration.
        """

        # FIXME: Move this to a ClassVar or global
        mapping = {'de_CH': 'german', 'fr_CH': 'french', 'it_CH': 'italian',
                   'rm_CH': 'english', None: 'english'}

        return self.__class__.match_term(
            column, mapping.get(locale, 'english'), term)

    if TYPE_CHECKING:
        # NOTE: This enforces the properties to be implemented in subclasses
        @property
        @abstractmethod
        def locale(self) -> str: ...

        @property
        @abstractmethod
        def term(self) -> str: ...

        @property
        @abstractmethod
        def term_filter_cols(self) -> dict[str, TextColumn]: ...
    else:
        @property
        def term_filter_cols(self) -> dict[str, TextColumn]:
            """ Returns a dict of column names to search in with term.
            Must be attributes of self.model_class.
            """
            raise NotImplementedError

    @property
    def term_filter(self) -> Iterator[ColumnElement[bool]]:
        assert self.term_filter_cols
        term = self.__class__.term_to_tsquery_string(self.term)

        return (
            self.filter_text_by_locale(
                getattr(self.model_class, col), term, self.locale)
            for col in self.term_filter_cols
        )

    def query(self) -> Query[_M]:
        if not self.term or not self.locale:
            return super().query()
        return super().query().filter(or_(*self.term_filter))


# FIXME: We are a little bit inconsistent about what's a base class
#        and what's a mixin and how we use it downstream, we should
#        probably try to clean that up a bit, so we always do it the
#        same way...
class Pagination(Generic[_M]):
    """ Provides collections with pagination, if they implement a few
    documented properties and methods.

    See :class:`onegov.ticket.TicketCollection` for an example.

    """

    batch_size = 10

    def __init__(self, page: int = 0):
        assert page is not None
        self.page = max(page, 0)

    def __eq__(self, other: object) -> bool:
        """ Returns True if the current and the other Pagination instance
        are equal. Used to find the current page in a list of pages.

        """
        raise NotImplementedError

    def subset(self) -> Query[_M]:
        """ Returns an SQLAlchemy query containing all records that should
        be considered for pagination.

        """
        raise NotImplementedError

    @cached_property
    def cached_subset(self) -> Query[_M]:
        return self.subset()

    if TYPE_CHECKING:
        # FIXME: This is dumb, why do we have the some property twice
        #        and we force one of them to be implemented but actually
        #        use and implement a different one downstream... clean
        #        this up.
        page: int

    @property
    def page_index(self) -> int:
        """ Returns the current page index (starting at 0). """
        raise NotImplementedError

    def page_by_index(self, index: int) -> Self:
        """ Returns the page at the given index. A page here means an instance
        of the class inheriting from the ``Pagination`` base class.

        """
        raise NotImplementedError

    def transform_batch_query(self, query: Query[_M]) -> Query[_M]:
        """ Allows subclasses to transform the given query before it is
        used to retrieve the batch. This is a good place to add additional
        loading that should only apply to the batch (say joining other
        values to the batch which are then not loaded by the whole query).

        """
        return query

    @cached_property
    def subset_count(self) -> int:
        """ Returns the total number of elements this pagination represents.

        """

        # the ordering is entirely unnecessary for a count, so remove it
        # to count things faster
        return self.cached_subset.order_by(None).count()

    @cached_property
    def batch(self) -> tuple[_M, ...]:
        """ Returns the elements on the current page. """
        query = self.cached_subset.slice(
            self.offset, self.offset + self.batch_size
        )
        return tuple(self.transform_batch_query(query))

    @property
    def offset(self) -> int:
        """ Returns the offset applied to the current subset. """
        return self.page * self.batch_size

    @property
    def pages_count(self) -> int:
        """ Returns the number of pages. """
        if not self.batch_size:
            return 1
        return math.ceil(self.subset_count / self.batch_size)

    @property
    def name_of_view(self) -> str:
        """The name of the view to link to. If omitted, the
        the default view is looked up.."""
        return ''

    @property
    def pages(self) -> Iterator[Self]:
        """ Yields all page objects of this Pagination. """
        for page in range(self.pages_count):
            yield self.page_by_index(page)

    @property
    def previous(self) -> Self | None:
        """ Returns the previous page or None. """
        if self.page - 1 >= 0:
            return self.page_by_index(self.page - 1)
        return None

    @property
    def next(self) -> Self | None:
        """ Returns the next page or None. """
        if self.page + 1 < self.pages_count:
            return self.page_by_index(self.page + 1)
        return None


class RangedPagination(Generic[_M]):
    """ Provides a pagination that supports loading multiple pages at once.

    This is useful in a context where a single button is used to 'load more'
    results one by one. In this case we need an URL that represents what's
    happening on the screen (multiple pages are shown at the same time).

    """

    # how many items are shown per page
    batch_size = 22

    # how many items may be shown together, ranges exceeding this limit are
    # may be clipped by using `limit_range`.
    range_limit = 5

    def subset(self) -> Query[_M]:
        """ Returns an SQLAlchemy query containing all records that should
        be considered for pagination.

        """
        raise NotImplementedError

    @cached_property
    def cached_subset(self) -> Query[_M]:
        return self.subset()

    @property
    def page_range(self) -> tuple[int, int]:
        """ Returns the current page range (starting at (0, 0)). """
        raise NotImplementedError

    def by_page_range(self, page_range: tuple[int, int]) -> Self:
        """ Returns an instance of the collection limited to the given
        page range.

        """
        raise NotImplementedError

    def limit_range(
        self,
        page_range: Sequence[int] | None,
        direction: Literal['up', 'down']
    ) -> tuple[int, int]:
        """ Limits the range to the range limit in the given direction.

        For example, 0-99 will be limited to 89-99 with a limit of 10 and 'up'.
        With 'down' it will be limited to 0-9.

        """
        assert direction in ('up', 'down')

        if not page_range:
            s, e = 0, 9
        elif len(page_range) == 1:
            s, e = page_range[0], page_range[0]
        else:
            s, e = page_range[:2]

        if e < s:
            s, e = e, s

        if (e - s) > self.range_limit:
            if direction == 'down':
                return s, s + self.range_limit
            else:
                return max(0, e - self.range_limit), e

        return (s, e)

    def transform_batch_query(self, query: Query[_M]) -> Query[_M]:
        """ Allows subclasses to transform the given query before it is
        used to retrieve the batch. This is a good place to add additional
        loading that should only apply to the batch (say joining other
        values to the batch which are then not loaded by the whole query).

        """
        return query

    @cached_property
    def subset_count(self) -> int:
        """ Returns the total number of elements this pagination represents.

        """

        # the ordering is entirely unnecessary for a count, so remove it
        # to count things faster
        return self.cached_subset.order_by(None).count()

    @cached_property
    def batch(self) -> tuple[_M, ...]:
        """ Returns the elements on the current page range. """
        s, e = self.page_range

        s = s * self.batch_size
        e = e * self.batch_size + self.batch_size

        query = self.cached_subset.slice(s, e)

        return tuple(self.transform_batch_query(query))

    @property
    def pages_count(self) -> int:
        """ Returns the number of pages. """
        if not self.batch_size:
            return 1

        return math.ceil(self.subset_count / self.batch_size)

    @property
    def previous(self) -> Self | None:
        """ Returns the previous page or None. """
        s, _e = self.page_range

        if s > 0:
            return self.by_page_range((s - 1, s - 1))
        return None

    @property
    def next(self) -> Self | None:
        """ Returns the next page range or None. """
        _s, e = self.page_range

        if e + 1 < self.pages_count:
            return self.by_page_range((e + 1, e + 1))
        return None
