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


class MoveDirection(Enum):
    """ Describs the possible directions for the
    :meth:`AdjacencyListCollection.move` method.

    """

    #: Moves the subject above the target
    above = 1

    #: Moves the subject below the target
    below = 2


def sort_siblings(siblings, key, reverse=False):
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
    id = Column(Integer, primary_key=True)

    #: the id of the parent
    @declared_attr
    def parent_id(cls):
        return Column(Integer, ForeignKey("{}.id".format(cls.__tablename__)))

    #: the name of the item - think of this as the id or better yet
    #: the url segment e.g. ``parent-item/child-item``
    #:
    #: automatically generated from the title if not provided
    name = Column(Text, nullable=False)

    #: the human readable title of the item
    title = Column(Text, nullable=False)

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    @declared_attr
    def children(cls):
        return relationship(
            cls.__name__,
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
    order = Column(Integer, default=2 ** 16)

    # default sort order is order, id
    @declared_attr
    def __mapper_args__(cls):
        return {
            "polymorphic_on": cls.type
        }

    @declared_attr
    def __table_args__(cls):

        return (
            # make sure that no children of a single parent share a name
            Index(
                cls.__name__.lower() + '_children_name', 'name', 'parent_id',
                unique=True, postgresql_where=column('parent_id') != None),

            # make sure that no root item shares the name with another
            #
            # this can't be combined with the index above because NULL values
            # in Postgres (and other SQL dbs) can't be unique in an index
            Index(
                cls.__name__.lower() + '_root_name', 'name', unique=True,
                postgresql_where=column('parent_id') == None),

            # have a sort index by parent/children as we often select by parent
            # and order by children/siblings
            Index(
                cls.__name__.lower() + '_order',
                nullsfirst('parent_id'),
                nullsfirst('"order"')
            )
        )

    @validates('name')
    def validate_name(self, key, name):
        assert normalize_for_url(name) == name, (
            "The given name was not normalized"
        )

        return name

    @property
    def sort_key(self):
        """ The sort key used for sorting the siblings if the title changes.

        """
        return AdjacencyListCollection.sort_key

    @declared_attr
    def sort_on_title_change(cls):
        """ Makes sure the A-Z sorting is kept when a title changes. """

        class OldItemProxy(Proxy):
            title = None

        # we need to wrap this here because this is an abstract base class
        @observes('title')
        def sort_on_title_change(self, title):

            # the title value has already changed at this point, and we
            # probably don't want to touch 'self' which is in transition,
            # so we create a sort key which fixes this for us, with an item
            # proxy that pretends to have the old value
            deleted = get_history(self, 'title').deleted

            if not deleted:
                return

            old_item = OldItemProxy(lambda: self)
            old_item.title = deleted[0]

            def old_sort_key(item):
                return self.sort_key(item is self and old_item or item)

            siblings = self.siblings.all()

            if is_sorted(siblings, key=old_sort_key):
                sort_siblings(siblings, key=self.sort_key)

        return sort_on_title_change

    def __init__(self, title, parent=None, **kwargs):
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
    def root(self):
        """ Returns the root of this item. """
        if self.parent is None:
            return self
        else:
            return self.parent.root

    @property
    def ancestors(self):
        """ Returns all ancestors of this item. """
        if self.parent:
            yield from self.parent.ancestors
            yield self.parent

    @property
    def siblings(self):
        """ Returns a query that includes all siblings, including the item
        itself.

        """
        query = object_session(self).query(self.__class__)
        query = query.order_by(self.__class__.order)
        query = query.filter(self.__class__.parent == self.parent)

        return query

    @property
    def path(self):
        """ Returns the path of this item. """
        return '/'.join(
            chain(
                (a.name for a in self.ancestors),
                (self.name, )
            )
        )

    @hybrid_property
    def absorb(self):
        """ Alias for :attr:`path`. This is a convenience feature for Morepath
        if a path is absorbed.

        See `<http://morepath.readthedocs.org/en/latest/\
        paths_and_linking.html?highlight=absorb#absorbing>`_

        """
        return self.path

    def __repr__(self):
        return "{}(name='{}', id={}, parent_id={})".format(
            self.__class__.__name__,
            self.name,
            self.id,
            self.parent_id
        )


class AdjacencyListCollection(object):
    """ A base class for collections working with :class:`AdjacencyList`. """

    @property
    def __listclass__(self):
        """ The list class this collection handles. Must inherit from
        :class:`AdjacencyList`.

        """
        raise NotImplementedError

    def __init__(self, session):
        self.session = session

    @staticmethod
    def sort_key(item):
        """ The sort key with which the items are sorted into their siblings.

        """
        return normalize_for_url(item.title)

    def query(self, ordered=True):
        """ Returns a query using
        :attr:`AdjacencyListCollection.__listclass__`.

        """
        query = self.session.query(self.__listclass__)
        query = ordered and query.order_by(self.__listclass__.order) or query

        return query

    @property
    def roots(self):
        """ Returns the root elements. """
        return self.query().filter(
            self.__listclass__.parent_id.is_(None)
        ).all()

    def by_id(self, item_id):
        """ Takes the given page id and returns the page. Try to keep this
        id away from the public. It's not a security problem if it leaks, but
        it's not something the public can necessarly count on.

        If possible use the path instead.

        """
        query = self.query(ordered=False)
        query = query.filter(self.__listclass__.id == item_id).first()

        return query

    def by_path(self, path, ensure_type=None):
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

        `<http://schinckel.net/2014/11/22/\
        postgres-tree-shootout-part-1%3A-introduction./>`

        `<http://schinckel.net/2014/11/27/\
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

    def get_unique_child_name(self, name, parent):
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

        names = set(
            s[0] for s in siblings.with_entities(self.__listclass__.name).all()
        )

        while name in names:
            name = increment_name(name)

        return name

    def add(self, parent, title, name=None, type=None, **kwargs):
        """ Adds a page to the given parent. """

        name = name or self.get_unique_child_name(title, parent)

        if type is not None:
            page_class = self.__listclass__.get_polymorphic_class(type)
        else:
            page_class = self.__listclass__

        page = page_class(parent=parent, title=title, name=name, **kwargs)

        self.session.add(page)
        self.session.flush()

        # impose an order, unless one is given
        if kwargs.get('order') is not None:
            return page

        siblings = page.siblings.all()

        if is_sorted((s for s in siblings if s != page), key=self.sort_key):
            sort_siblings(siblings, key=self.sort_key)

        return page

    def add_root(self, title, name=None, **kwargs):
        return self.add(None, title, name, **kwargs)

    def add_or_get(self, parent, title, name=None, **kwargs):

        name = name or normalize_for_url(title)

        query = self.query(ordered=False)
        query = query.filter(self.__listclass__.parent == parent)
        query = query.filter(self.__listclass__.name == name)

        item = query.first()

        if item:
            return item
        else:
            return self.add(parent, title, name, **kwargs)

    def add_or_get_root(self, title, name=None, **kwargs):
        return self.add_or_get(None, title, name, **kwargs)

    def delete(self, page):
        """ Deletes the given page and *all* it's desecendants!. """
        self.session.delete(page)
        self.session.flush()

    def move_above(self, subject, target):
        return self.move(subject, target, MoveDirection.above)

    def move_below(self, subject, target):
        return self.move(subject, target, MoveDirection.below)

    def move(self, subject, target, direction):
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

        def new_order():
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
