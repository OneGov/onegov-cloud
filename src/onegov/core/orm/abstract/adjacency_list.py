from enum import Enum
from itertools import chain
from lazy_object_proxy import Proxy
from onegov.core.orm import Base
from onegov.core.utils import normalize_for_url, increment_name, is_sorted
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    backref,
    object_session,
    relationship,
    validates
)
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.schema import Index
from sqlalchemy.sql.expression import column, nullsfirst
from sqlalchemy_utils import observes


from typing import Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from sqlalchemy.orm.query import Query
    from sqlalchemy.orm.session import Session
    from typing_extensions import Self
    from _typeshed import SupportsRichComparison


_L = TypeVar('_L', bound='AdjacencyList')


class MoveDirection(Enum):
    """ Describs the possible directions for the
    :meth:`AdjacencyListCollection.move` method.

    """

    #: Moves the subject above the target
    above = 1

    #: Moves the subject below the target
    below = 2


def sort_siblings(
    siblings: 'Sequence[_L]',
    key: 'Callable[[_L], SupportsRichComparison]',
    reverse: bool = False
) -> None:
    """ Sorts the siblings by the given key, writing the order to the
    database.

    """
    new_order = sorted(siblings, key=key, reverse=reverse)

    for ix, sibling in enumerate(new_order):
        sibling.order = ix


class AdjacencyList(Base):
    """ An abstract AdjacencyList implementation representing a Tree. """

    __abstract__ = True

    #: the id fo the db record (only relevant internally)
    #: do not change this id after creation as that would destroy the tree
    id: 'Column[int]' = Column(Integer, primary_key=True)

    if TYPE_CHECKING:
        parent_id: 'Column[int | None]'
        # subclasses need to override with the correct relationship
        # with generics there's an issue with class vs instance access
        # technically AdjacencyList is abstract, so as long as we force
        # subclasses to bind a type we could make this type safe, but
        # there is no way to express this in mypy, we could write a
        # mypy plugin to ensure these relationships get generated
        # properly...
        parent: 'relationship[AdjacencyList | None]'
        children: 'relationship[Sequence[AdjacencyList]]'

    #: the id of the parent
    @declared_attr  # type:ignore[no-redef]
    def parent_id(cls) -> 'Column[int | None]':
        return Column(Integer, ForeignKey("{}.id".format(cls.__tablename__)))

    #: the name of the item - think of this as the id or better yet
    #: the url segment e.g. ``parent-item/child-item``
    #:
    #: automatically generated from the title if not provided
    name: 'Column[str]' = Column(Text, nullable=False)

    #: the human readable title of the item
    title: 'Column[str]' = Column(Text, nullable=False)

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: 'Column[str]' = Column(
        Text, nullable=False, default=lambda: 'generic')

    @declared_attr  # type:ignore[no-redef]
    def children(cls) -> 'relationship[list[Self]]':
        return relationship(
            cls.__name__,  # type:ignore[attr-defined]
            order_by=cls.order,

            # cascade deletions - it's not the job of this model to prevent
            # the user from deleting all his content
            cascade="all, delete-orphan",

            # many to one + adjacency list - remote_side
            # is required to reference the 'remote'
            # column in the join condition.
            backref=backref("parent", remote_side=cls.id)
        )

    #: the order of the items - items are added at the end by default
    # FIXME: This should probably have been nullable=False
    order: 'Column[int]' = Column(Integer, default=2 ** 16)

    # default sort order is order, id
    @declared_attr
    def __mapper_args__(cls):  # type:ignore
        return {
            'polymorphic_on': cls.type,
            'polymorphic_identity': 'generic'
        }

    @declared_attr
    def __table_args__(cls):  # type:ignore

        prefix = cls.__name__.lower()
        return (
            # make sure that no children of a single parent share a name
            Index(
                prefix + '_children_name', 'name', 'parent_id',
                unique=True, postgresql_where=column('parent_id') != None),

            # make sure that no root item shares the name with another
            #
            # this can't be combined with the index above because NULL values
            # in Postgres (and other SQL dbs) can't be unique in an index
            Index(
                prefix + '_root_name', 'name', unique=True,
                postgresql_where=column('parent_id') == None),

            # have a sort index by parent/children as we often select by parent
            # and order by children/siblings
            Index(
                prefix + '_order',
                nullsfirst('parent_id'),
                nullsfirst('"order"')
            )
        )

    @validates('name')
    def validate_name(self, key: None, name: str) -> str:
        assert normalize_for_url(name) == name, (
            "The given name was not normalized"
        )

        return name

    @property
    def sort_key(self) -> 'Callable[[Self], SupportsRichComparison]':
        """ The sort key used for sorting the siblings if the title changes.

        """
        return AdjacencyListCollection.sort_key

    if TYPE_CHECKING:
        @observes('title')
        def sort_on_title_change(self, title: str) -> None: ...

    @declared_attr  # type:ignore[no-redef]
    def sort_on_title_change(  # noqa: F811
        cls
    ) -> 'Callable[[Self, str], None]':
        """ Makes sure the A-Z sorting is kept when a title changes. """

        class OldItemProxy(Proxy):
            title = None

        # we need to wrap this here because this is an abstract base class
        @observes('title')
        def sort_on_title_change(self: 'Self', title: str) -> None:

            # the title value has already changed at this point, and we
            # probably don't want to touch 'self' which is in transition,
            # so we create a sort key which fixes this for us, with an item
            # proxy that pretends to have the old value
            deleted = get_history(self, 'title').deleted

            if not deleted:
                return

            old_item = OldItemProxy(lambda: self)
            old_item.title = deleted[0]

            def old_sort_key(item: 'Self') -> 'SupportsRichComparison':
                return self.sort_key(item is self and old_item or item)

            siblings = self.siblings.all()

            if is_sorted(siblings, key=old_sort_key):
                sort_siblings(siblings, key=self.sort_key)

        return sort_on_title_change

    def __init__(
        self,
        title: str,
        parent: 'Self | None' = None,
        **kwargs: Any
    ):
        """ Initializes a new item with the given title. If no parent
        is passed, the item is a root item.

        """
        self.title = title
        self.parent = parent

        # makes sure the parent_id is availble without flushing
        if parent:
            self.parent_id = parent.id

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def root(self) -> 'AdjacencyList':
        """ Returns the root of this item. """
        if self.parent is None:
            return self
        else:
            return self.parent.root

    @property
    def ancestors(self) -> 'Iterator[AdjacencyList]':
        """ Returns all ancestors of this item. """
        if self.parent:
            yield from self.parent.ancestors
            yield self.parent

    @property
    def siblings(self) -> 'Query[Self]':
        """ Returns a query that includes all siblings, including the item
        itself.

        """

        # FIXME: There is a subtle issue here if we use this mixin in a
        #        polymorphic class, since it will only return siblings of
        #        the same polymorphic type, which is probably not what
        #        we want, since it doesn't match the behavior of root
        #        ancestors, parent, children, etc. We could use inspect
        #        to determine whether or not the model is polymorphic
        #        and to retrieve the base class.
        query = object_session(self).query(self.__class__)
        query = query.order_by(self.__class__.order)
        query = query.filter(self.__class__.parent == self.parent)

        return query

    @property
    def path(self) -> str:
        """ Returns the path of this item. """
        return '/'.join(
            chain(
                (a.name for a in self.ancestors),
                (self.name, )
            )
        )

    @hybrid_property
    def absorb(self) -> str:
        """ Alias for :attr:`path`. This is a convenience feature for Morepath
        if a path is absorbed.

        See `<https://morepath.readthedocs.org/en/latest/\
        paths_and_linking.html?highlight=absorb#absorbing>`_

        """
        return self.path

    def __repr__(self) -> str:
        return "{}(name='{}', id={}, parent_id={})".format(
            self.__class__.__name__,
            self.name,
            self.id,
            self.parent_id
        )


class AdjacencyListCollection(Generic[_L]):
    """ A base class for collections working with :class:`AdjacencyList`. """

    @property
    def __listclass__(self) -> type[_L]:
        """ The list class this collection handles. Must inherit from
        :class:`AdjacencyList`.

        """
        raise NotImplementedError

    def __init__(self, session: 'Session'):
        self.session = session

    @staticmethod
    def sort_key(item: _L) -> 'SupportsRichComparison':
        """ The sort key with which the items are sorted into their siblings.

        """
        return normalize_for_url(item.title)

    def query(self, ordered: bool = True) -> 'Query[_L]':
        """ Returns a query using
        :attr:`AdjacencyListCollection.__listclass__`.

        """
        query = self.session.query(self.__listclass__)
        query = ordered and query.order_by(self.__listclass__.order) or query

        return query

    @property
    def roots(self) -> list[_L]:
        """ Returns the root elements. """
        return self.query().filter(
            self.__listclass__.parent_id.is_(None)
        ).all()

    def by_id(self, item_id: int) -> _L | None:
        """ Takes the given page id and returns the page. Try to keep this
        id away from the public. It's not a security problem if it leaks, but
        it's not something the public can necessarly count on.

        If possible use the path instead.

        """
        query = self.query(ordered=False)
        item = query.filter(self.__listclass__.id == item_id).first()
        return item

    def by_path(self, path: str, ensure_type: str | None = None) -> _L | None:
        """ Takes a path and returns the page associated with it.

        For example, given this hierarchy::

            Page(name='documents', id=0, parent_id=None)
                Page(name='readme', id=1, parent_id=0)
                Page(name='license', id=2, parent_id=0)

        The following query would return the Page with the name 'license'::

            paths.by_path('documents/license')

        Slashes at the beginning or end are ignored, so the above is equal to::

            paths.by_path('/documents/license')
            paths.by_path('/documents/license/')
            paths.by_path('documents/license/')

        Lookups by path are currently quite wasteful. To get the root of
        a page nested deeply one has to walk the ascendants of the page one by
        one, triggering a number of queries.

        Should this actually become a bottleneck (it might be fine), we should
        probably implement a materialized view that is updated whenever a page
        changes.

        See:

        `<https://schinckel.net/2014/11/22/\
        postgres-tree-shootout-part-1%3A-introduction./>`

        `<https://schinckel.net/2014/11/27/\
        postgres-tree-shootout-part-2%3A-adjacency-list-using-ctes/>`

        """

        fragments = path.strip('/').split('/')

        item = self.query(ordered=False).filter(
            self.__listclass__.name == fragments.pop(0),
            self.__listclass__.parent_id == None
        ).first()

        while item and fragments:
            item = self.query(ordered=False).filter(
                self.__listclass__.name == fragments.pop(0),
                self.__listclass__.parent_id == item.id
            ).first()

        if ensure_type is None or item is None or item.type == ensure_type:
            return item
        return None

    def get_unique_child_name(self, name: str, parent: _L | None) -> str:
        """ Takes the given name or title, normalizes it and makes sure
        that it's unique among the siblings of the item.

        This is achieved by adding numbers at the end if there are overlaps.

        For example, ``root`` becomes ``root-1`` if ``root`` exists. ``root-2``
        if ``root-1`` exists and so on.

        """
        name = normalize_for_url(name)
        name = name or 'page'

        siblings = self.query(ordered=False).filter(
            self.__listclass__.parent == parent)

        names = {
            n for n, in siblings.with_entities(self.__listclass__.name)
        }

        while name in names:
            name = increment_name(name)

        return name

    # NOTE: We are trusting that you do no evil and only create subclasses
    #       of the list class bound to this collection, but we can't really
    #       verify that statically very well. `parent` does give us a hint
    #       but you can still set `type` to whatever you want...
    def add(
        self,
        parent: _L | None,
        title: str,
        name: str | None = None,
        type: str | None = None,
        **kwargs: Any
    ) -> _L:
        """ Adds a child to the given parent. """

        name = name or self.get_unique_child_name(title, parent)

        if type is not None:
            child_class = self.__listclass__.get_polymorphic_class(type)
        else:
            child_class = self.__listclass__

        child = child_class(parent=parent, title=title, name=name, **kwargs)

        self.session.add(child)

        # impose an order, unless one is given
        if kwargs.get('order') is not None:
            self.session.flush()
            return child

        siblings = child.siblings.all()

        if is_sorted((s for s in siblings if s != child), key=self.sort_key):
            sort_siblings(siblings, key=self.sort_key)

        self.session.flush()
        return child

    def add_root(
        self,
        title: str,
        name: str | None = None,
        **kwargs: Any
    ) -> _L:
        return self.add(None, title, name, **kwargs)

    def add_or_get(
        self,
        parent: _L | None,
        title: str,
        name: str | None = None,
        **kwargs: Any
    ) -> _L:

        name = name or normalize_for_url(title)

        query = self.query(ordered=False)
        query = query.filter(self.__listclass__.parent == parent)
        query = query.filter(self.__listclass__.name == name)

        item = query.first()

        if item:
            return item
        else:
            return self.add(parent, title, name, **kwargs)

    def add_or_get_root(
        self,
        title: str,
        name: str | None = None,
        **kwargs: Any
    ) -> _L:
        return self.add_or_get(None, title, name, **kwargs)

    def delete(self, item: _L) -> None:
        """ Deletes the given item and *all* it's desecendants!. """
        self.session.delete(item)
        self.session.flush()

    def move_above(self, subject: _L, target: _L) -> None:
        return self.move(subject, target, MoveDirection.above)

    def move_below(self, subject: _L, target: _L) -> None:
        return self.move(subject, target, MoveDirection.below)

    def move(self, subject: _L, target: _L, direction: MoveDirection) -> None:
        """ Takes the given subject and moves it somehwere in relation to the
        target.

        :subject:
            The item to be moved.

        :target:
            The item above which or below which the subject is moved.

        :direction:
            The direction relative to the target. Either
            :attr:`MoveDirection.above` if the subject should be moved
            above the target, or :attr:`MoveDirection.below` if the subject
            should be moved below the target.

        """
        assert direction in MoveDirection
        assert subject != target

        # we might allow for something like this in the future, but for now
        # we keep it safe and simple
        assert target.parent_id == subject.parent_id, (
            "The subject's and the target's parent must be the same. This "
            "includes root nodes (both should have no parent)."
        )

        siblings = target.siblings.all()

        def new_order() -> 'Iterator[_L]':
            for sibling in siblings:
                if sibling == subject:
                    continue

                if sibling == target and direction == MoveDirection.above:
                    yield subject
                    yield target
                    continue

                if sibling == target and direction == MoveDirection.below:
                    yield target
                    yield subject
                    continue

                yield sibling

        for order, sibling in enumerate(new_order()):
            sibling.order = order


ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NUMERIC_PRIORITY_TRANS = str.maketrans({
    'Ä': 'AE',
    'Ö': 'OE',
    'Ü': 'UE',
    '0': 'B',
    '1': 'B',
    '2': 'C',
    '3': 'D',
    '4': 'E',
    '5': 'F',
    '6': 'G',
    '7': 'H',
    '8': 'I',
    '9': 'J'
})


def numeric_priority(string: str | None, max_len: int = 4) -> int | None:
    """ Transforms a alphabetical order into a numeric value that can be
    used for the ordering of the siblings.
    German Umlaute and also numbers are supported.
    """
    if not string:
        return None

    repl_string = string.upper().translate(NUMERIC_PRIORITY_TRANS)
    pows = list(reversed(range(max_len)))
    return sum(
        (ALPHABET.index(letter) + 1) * pow(10, pows[i])
        for i, letter in enumerate(repl_string)
    )
