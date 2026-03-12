from __future__ import annotations

from enum import Enum
from decimal import Decimal
from collections.abc import Callable
from itertools import chain
from lazy_object_proxy import Proxy  # type:ignore[import-untyped]
from onegov.core.orm import Base, observes
from onegov.core.utils import is_sorted, normalize_for_url, increment_name
from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    object_session,
    mapped_column,
    relationship,
    validates,
    Mapped
)
from sqlalchemy.orm.attributes import get_history
from sqlalchemy.schema import Index
from sqlalchemy.sql.expression import column, nullsfirst


from typing import overload, Any, Generic, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from sqlalchemy.orm.query import Query
    from sqlalchemy.orm.session import Session
    from typing import Self
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
    siblings: Sequence[_L],
    key: Callable[[_L], SupportsRichComparison],
    reverse: bool = False
) -> None:
    """ Sorts the siblings by the given key, writing the order to the
    database.

    """
    new_order = sorted(siblings, key=key, reverse=reverse)

    for ix, sibling in enumerate(new_order):
        sibling.order = Decimal(ix)


class AdjacencyList(Base):
    """ An abstract AdjacencyList implementation representing a Tree. """

    __abstract__ = True

    #: the id fo the db record (only relevant internally)
    #: do not change this id after creation as that would destroy the tree
    id: Mapped[int] = mapped_column(primary_key=True)

    #: the id of the parent
    @declared_attr
    @classmethod
    def parent_id(cls) -> Mapped[int | None]:
        return mapped_column(
            ForeignKey(f'{cls.__tablename__}.id')
        )

    #: the name of the item - think of this as the id or better yet
    #: the url segment e.g. ``parent-item/child-item``
    #:
    #: automatically generated from the title if not provided
    name: Mapped[str]

    #: the human readable title of the item
    title: Mapped[str]

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: Mapped[str] = mapped_column(default=lambda: 'generic')

    # subclasses need to override with the correct relationship
    # with generics there's an issue with class vs instance access
    # technically AdjacencyList is abstract, so as long as we force
    # subclasses to bind a type we could make this type safe, but
    # there is no way to express this in mypy, we could write a
    # mypy plugin to ensure these relationships get generated
    # properly...
    @declared_attr
    @classmethod
    def children(cls) -> Mapped[list[Self]]:
        return relationship(
            cls.__name__,
            order_by=cls.order,
            # cascade deletions - it's not the job of this model to prevent
            # the user from deleting all his content
            cascade='all, delete-orphan',
            back_populates='parent'
        )

    @declared_attr
    @classmethod
    def parent(cls) -> Mapped[Self | None]:
        return relationship(
            cls.__name__,
            # many to one + adjacency list - remote_side
            # is required to reference the 'remote'
            # column in the join condition.
            remote_side=cls.id,
            back_populates='children'
        )

    #: the order of the items - items are added at the end by default
    # FIXME: This should probably have been nullable=False
    order: Mapped[Decimal] = mapped_column(
        Numeric(precision=30, scale=15),
        default=Decimal('65536')  # Default middle value (2**16)
    )

    # default sort order is order, id
    @declared_attr.directive
    @classmethod
    def __mapper_args__(cls) -> dict[str, Any]:
        return {
            'polymorphic_on': cls.type,
            'polymorphic_identity': 'generic'
        }

    @declared_attr.directive
    @classmethod
    def __table_args__(cls) -> tuple[Any, ...]:

        prefix: str = cls.__name__.lower()
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
                nullsfirst('parent_id'),  # type:ignore[arg-type]
                nullsfirst('"order"')  # type:ignore[arg-type]
            )
        )

    @validates('name')
    def validate_name(self, key: None, name: str) -> str:
        assert normalize_for_url(name) == name, (
            'The given name was not normalized'
        )

        return name

    @property
    def sort_key(self) -> Callable[[Self], SupportsRichComparison]:
        """ The sort key used for sorting the siblings if the title changes.

        """
        return AdjacencyListCollection.sort_key

    @declared_attr.directive
    @classmethod
    def sort_on_title_change(cls) -> Callable[[Self, str], None]:
        """ Makes sure the A-Z sorting is kept when a title changes. """

        class OldItemProxy(Proxy):  # type:ignore[misc]
            title = None

        # we need to wrap this here because this is an abstract base class
        @observes('title')
        def sort_on_title_change(self: Self, title: str) -> None:

            # the title value has already changed at this point, and we
            # probably don't want to touch 'self' which is in transition,
            # so we create a sort key which fixes this for us, with an item
            # proxy that pretends to have the old value
            deleted = get_history(self, 'title').deleted

            if not deleted:
                return

            old_item = OldItemProxy(lambda: self)
            old_item.title = deleted[0]

            def old_sort_key(item: Self) -> SupportsRichComparison:
                return self.sort_key(item is self and old_item or item)

            siblings = self.siblings.all()

            # Check if the list *was* sorted according to the *old* title
            if is_sorted(siblings, key=old_sort_key):
                calculuate_midpoint_order(siblings, self, self.sort_key)

        return sort_on_title_change

    if not TYPE_CHECKING:
        # NOTE: Avoids confusing SQLAlchemy
        del sort_on_title_change.fget.__annotations__

    def __init__(
        self,
        title: str,
        parent: Self | None = None,
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
    def root(self) -> AdjacencyList:
        """ Returns the root of this item. """
        if self.parent is None:
            return self
        else:
            return self.parent.root

    @property
    def ancestors(self) -> Iterator[AdjacencyList]:
        """ Returns all ancestors of this item. """
        if self.parent:
            yield from self.parent.ancestors
            yield self.parent

    @property
    def siblings(self) -> Query[Self]:
        """ Returns a query that includes all siblings, including the item
        itself.

        """
        session = object_session(self)
        assert session is not None

        # FIXME: There is a subtle issue here if we use this mixin in a
        #        polymorphic class, since it will only return siblings of
        #        the same polymorphic type, which is probably not what
        #        we want, since it doesn't match the behavior of root
        #        ancestors, parent, children, etc. We could use inspect
        #        to determine whether or not the model is polymorphic
        #        and to retrieve the base class.
        query = session.query(self.__class__)
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


def calculuate_midpoint_order(
    siblings: list[_L], new_item: _L, key: Callable[[_L], Any]
) -> None:
    """Insert/update an item's order """
    left, right = None, None
    new_item_key_val = key(new_item)

    # Find the logical position in the key-sorted list
    for neighbor in siblings:
        if neighbor == new_item:
            continue
        neighbor_key_val = key(neighbor)
        if neighbor_key_val > new_item_key_val:
            # This neighbor comes after the new item
            right = neighbor
            # The previous neighbor (if any) is the left one
            # 'left' remains from the previous iteration
            break
        else:
            # This neighbor comes before or is equal, update left
            left = neighbor

    # Calculate new order value
    if left and right:
        # Between two neighbors
        left_order = Decimal(str(left.order))
        right_order = Decimal(str(right.order))
        # Check for potential precision issues or identical orders
        if left_order == right_order:
            # This indicates a problem or requires re-numbering.
            # For now, let's place it slightly after left.
            # A more robust solution might involve re-spacing siblings.
            new_item.order = left_order + Decimal(
                '0.000000000000001'
            )  # Tiny increment
        else:
            new_item.order = (left_order + right_order) / 2
    elif left:
        # After last item (based on key)
        new_item.order = Decimal(str(left.order)) + Decimal(
            '1'
        )  # Increment from left
    elif right:
        # Before first item (based on key)
        new_item.order = (
            Decimal(str(right.order)) / 2
        )  # Half of the first item's order
    else:
        # Only item in the list (or all others filtered out)
        new_item.order = Decimal('65536')  # Default middle value


class AdjacencyListCollection(Generic[_L]):
    """ A base class for collections working with :class:`AdjacencyList`. """

    @property
    def __listclass__(self) -> type[_L]:
        """ The list class this collection handles. Must inherit from
        :class:`AdjacencyList`.

        """
        raise NotImplementedError

    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def sort_key(item: _L) -> SupportsRichComparison:
        """ The sort key with which the items are sorted into their siblings.

        """
        return normalize_for_url(item.title)

    def query(self, ordered: bool = True) -> Query[_L]:
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
        **kwargs: Any,
    ) -> _L:
        """Adds a child.
        - If order is explicit, uses it.
        - If siblings are sorted by sort_key, inserts starting form mid
        - If siblings are NOT sorted by sort_key, append at the end
        """
        name = name or self.get_unique_child_name(title, parent)

        if type is not None:
            child_class = self.__listclass__.get_polymorphic_class(type)
        else:
            child_class = self.__listclass__

        # Handle explicit order passed directly or via kwargs
        explicit_order = kwargs.pop('order', None)
        if explicit_order is not None:
            # Ensure it's Decimal before passing to constructor
            kwargs['order'] = Decimal(str(explicit_order))

        child = child_class(parent=parent, title=title, name=name, **kwargs)
        self.session.add(child)
        # Flush required to get child.id for sibling query and relationship
        # loading
        self.session.flush()

        # If order was NOT explicitly provided, decide insertion strategy
        if explicit_order is None:
            siblings: list[_L] = child.siblings.all()
            existing_siblings: list[_L] = [s for s in siblings if s != child]

            if not existing_siblings or is_sorted(
                existing_siblings, key=self.sort_key
            ):
                # --- Strategy 1: Insert based on title key ---
                calculuate_midpoint_order(siblings, child, self.sort_key)
            else:
                # --- Strategy 2: Append numerically at the end ---
                child.order = max(
                    (s.order for s in existing_siblings if s.order
                        is not None),
                    default=Decimal('65535'),
                ) + Decimal('1')

            # Flush again only if order was calculated (not explicit)
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

        try:
            target_index = siblings.index(target)
        except ValueError as err:
            raise ValueError(
                'Target not found in its own siblings list .'
            ) from err

        left, right = None, None

        # Determine the neighbors based on the *current* order
        if direction == MoveDirection.above:
            # Place subject *before* target
            right = target
            # Find the sibling immediately before target (if any)
            # This sibling must not be the subject itself
            potential_left_index = target_index - 1
            while potential_left_index >= 0:
                if siblings[potential_left_index] != subject:
                    left = siblings[potential_left_index]
                    break
                potential_left_index -= 1

        elif direction == MoveDirection.below:
            # Place subject *after* target
            left = target
            # Find the sibling immediately after target (if any)
            # This sibling must not be the subject itself
            potential_right_index = target_index + 1
            while potential_right_index < len(siblings):
                if siblings[potential_right_index] != subject:
                    right = siblings[potential_right_index]
                    break
                potential_right_index += 1

        if left and right:
            left_order = Decimal(str(left.order))
            right_order = Decimal(str(right.order))
            # Check for duplicate orders or precision issues
            if left_order == right_order:
                # Handle collision - maybe re-number or place slightly offset
                subject.order = left_order + Decimal('0.000000000000001')
            else:
                subject.order = (left_order + right_order) / 2
        elif left:
            # Place after left (target was left, or target was last)
            subject.order = Decimal(str(left.order)) + Decimal('1')
        elif right:
            # Place before right (target was right, or target was first)
            subject.order = Decimal(str(right.order)) / 2
        else:
            # This case (no left and no right) should only happen if the target
            # is the only sibling (excluding subject). Place subject with
            # default.
            subject.order = Decimal('65536')
        # The subject.order is now updated. Caller should flush/commit.


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


# NOTE: As mypy correctly complains these overloads are not safe, but using
#       this function as a sort key would be very annoying without this
#       safety hole. (The unsafety occurs when the runtime value for `str`
#       is the empty string, since the first overload should match, but
#       there's no way for the type checker to know that)
@overload
def numeric_priority(string: Literal[''] | None, max_len: int = 4) -> None: ...  # type: ignore[overload-overlap]
@overload
def numeric_priority(string: str, max_len: int = 4) -> int: ...


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
