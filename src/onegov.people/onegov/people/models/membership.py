from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


class AgencyMembership(Base, ContentMixin, TimestampMixin, ORMSearchable):
    """ A membership to an agency. """

    __tablename__ = 'agency_memberships'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': None,
    }

    es_public = True
    es_properties = {
        'title': {'type': 'text'},
    }

    #: the unique id, part of the url
    id = Column(UUID, primary_key=True, default=uuid4)

    #: the id of the agency
    agency_id = Column(
        Integer,
        ForeignKey('agencies.id'),
        nullable=False
    )

    #: the related agency (which may have any number of memberships)
    agency = relationship(
        'Agency',
        backref=backref(
            'memberships',
            cascade='all, delete-orphan',
            lazy='dynamic',
            order_by='AgencyMembership.order'
        )
    )

    #: the id of the person
    person_id = Column(UUID, ForeignKey('people.id'), nullable=False)

    #: the related person (which may have any number of memberships)
    person = relationship(
        'Person',
        backref=backref(
            'memberships',
            cascade='all, delete-orphan',
            lazy='dynamic',
        )
    )

    #: the position of the membership within the agency
    order = Column(Integer, nullable=False)

    #: describes the membership
    title = Column(Text, nullable=False)

    #: when the membership started
    since = Column(Text, nullable=True)

    @property
    def siblings(self):
        """ Returns a query that includes all siblings, including the item
        itself.

        """
        query = object_session(self).query(self.__class__)
        query = query.order_by(self.__class__.order)
        query = query.filter(self.__class__.agency == self.agency)
        return query
