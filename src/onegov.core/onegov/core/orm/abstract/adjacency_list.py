from itertools import chain
from onegov.core.orm import Base
from onegov.core.utils import normalize_for_url, increment_name
from sqlalchemy import Column, ForeignKey, Integer, Text, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    backref,
    object_session,
    relationship,
    validates
)
from sqlalchemy.schema import Index
from sqlalchemy.sql.expression import column


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
                postgresql_where=column('parent_id') == None)
        )

    @validates('name')
    def validate_name(self, key, name):
        assert normalize_for_url(name) == name, (
            "The given name was not normalized"
        )

        return name

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
            for ancestor in self.parent.ancestors:
                yield ancestor

            yield self.parent

    @property
    def siblings(self):
        """ Returns a query that includes all siblings, including the item
        itself.

        """
        query = object_session(self).query(self.__class__)
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

    def query(self):
        """ Returns a query using
        :attr:`AdjacencyListCollection.__listclass__`.

        """
        return self.session.query(self.__listclass__)

    def by_id(self, item_id):
        """ Takes the given page id and returns the page. Try to keep this
        id away from the public. It's not a security problem if it leaks, but
        it's not something the public can necessarly count on.

        If possible use the path instead.

        """
        return self.query().filter(self.__listclass__.id == item_id).first()

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

        item = self.query().filter(
            self.__listclass__.name == fragments.pop(0),
            self.__listclass__.parent_id == None
        ).first()

        while item and fragments:
            item = self.query().filter(
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

        siblings = self.query().filter(self.__listclass__.parent == parent)
        names = set(
            s[0] for s in siblings.with_entities(self.__listclass__.name).all()
        )

        while name in names:
            name = increment_name(name)

        return name

    def add(self, parent, title, name=None, **kwargs):
        """ Adds a page to the given parent. """

        name = name or self.get_unique_child_name(title, parent)

        # look up the right class depending on the type
        page_mapper = inspect(self.__listclass__).polymorphic_map.get(
            kwargs.get('type'))

        page_class = page_mapper and page_mapper.class_ or self.__listclass__

        page = page_class(parent=parent, title=title, name=name, **kwargs)

        self.session.add(page)
        self.session.flush()

        return page

    def add_root(self, title, name=None, **kwargs):
        return self.add(None, title, name, **kwargs)

    def add_or_get(self, parent, title, name=None, **kwargs):

        name = name or normalize_for_url(title)

        query = self.query().filter(self.__listclass__.parent == parent)
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

    def move(self, page, new_parent):
        """ Takes the given page and moves it under the new_parent. """
        page.parent = new_parent
        self.session.flush()
