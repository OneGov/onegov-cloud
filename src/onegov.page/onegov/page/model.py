""" A OneGov Page is an Adjacency List used to represent pages with any kind
of content in a hierarchy.

See also: `<http://docs.sqlalchemy.org/en/rel_0_9/orm/self_referential.html>`_

"""

from itertools import chain
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON
from onegov.core.utils import normalize_for_url
from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    backref,
    deferred,
    object_session,
    relationship,
    validates
)
from sqlalchemy.schema import Index
from sqlalchemy.sql.expression import column


class Page(Base, TimestampMixin):
    """ Defines a generic page. """

    __tablename__ = 'pages'

    #: the id fo the db record (only relevant internally)
    #: do not change this id after creation as that would destroy the tree
    id = Column(Integer, primary_key=True)

    #: the id of the parent page
    parent_id = Column(Integer, ForeignKey(id))

    #: the name of the page - think of this as the id or better yet
    #: the url segment e.g. ``pages/my-page-name``
    #:
    #: automatically generated from the title if not provided
    name = Column(Text, nullable=False)

    #: the human readable title of the page
    title = Column(Text, nullable=False)

    #: the type of the page, this can be used to create custom polymorphic
    #: subclasses of Page. See `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    #: metdata associated with the page - the size of it should be kept small
    #: as metadata is loaded with every query by default
    #:
    #: you want a page type or a short description here, but not a phd thesis
    #: or star trek fanfiction
    #:
    #: we would use 'metadata' here as a name, but that name is reserved
    #: by SQLAlchemy and can't be used by us
    meta = Column(JSON, nullable=False, default=dict)

    #: content associated with the page - not loaded by default so this one is
    #: useful for actually storing large bodies of data
    content = deferred(Column(JSON, nullable=False, default=dict))

    #: the child pages of this page
    children = relationship(
        "Page",

        # cascade deletions - it's not the job of this model to prevent
        # the user from deleting all his content
        cascade="all, delete-orphan",

        # many to one + adjacency list - remote_side
        # is required to reference the 'remote'
        # column in the join condition.
        backref=backref("parent", remote_side=id)
    )

    #: the order of the pages - pages are added at the end by default
    order = Column(Integer, default=2 ** 16)

    # default sort order is order, id
    __mapper_args__ = {
        "order_by": [order, id],
        "polymorphic_on": 'type'
    }

    __table_args__ = (
        # make sure that no children of a single parent share a name
        Index(
            'children_name', 'name', 'parent_id', unique=True,
            postgresql_where=column('parent_id') != None),
        # make sure that no root page shares the name with another
        #
        # this can't be combined with the index above because NULL value's in
        # Postgres (and other SQL dbs) can't be unique in an index
        Index(
            'root_name', 'name', unique=True,
            postgresql_where=column('parent_id') == None)
    )

    @validates('name')
    def validate_name(self, key, name):
        assert normalize_for_url(name) == name, (
            "The given name was not normalized"
        )

        return name

    def __init__(self, title, parent=None, **kwargs):
        """ Initializes a new page with the given title. If no parent
        is passed, the page is a root page.

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
        """ Returns the root of this page. """
        if self.parent is None:
            return self
        else:
            return self.parent.root

    @property
    def ancestors(self):
        """ Returns all ancestors of this page. """
        if self.parent:
            for ancestor in self.parent.ancestors:
                yield ancestor

            yield self.parent

    @property
    def siblings(self):
        """ Returns a query that includes all siblings, including the page
        itself.

        """
        query = object_session(self).query(Page)
        query = query.filter(Page.parent == self.parent)

        return query

    @property
    def path(self):
        """ Returns the path of this page. """
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
        return "Page(name=%r, id=%r, parent_id=%r)" % (
            self.name,
            self.id,
            self.parent_id
        )
