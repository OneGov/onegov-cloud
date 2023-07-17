from sqlalchemy.dialects.postgresql import TSVECTOR

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable, Searchable
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .agency import Agency
    from .person import Person


class AgencyMembership(Base, ContentMixin, TimestampMixin, ORMSearchable,
                       UTCPublicationMixin):
    """ A membership to an agency. """

    __tablename__ = 'agency_memberships'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=False, default=lambda: 'generic')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
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
    agency: 'relationship[Agency]' = relationship(
        'Agency',
        backref=backref(
            'memberships',
            cascade='all, delete-orphan',
            lazy='dynamic',
            order_by='AgencyMembership.order_within_agency'
        )
    )

    #: the id of the person
    person_id = Column(UUID, ForeignKey('people.id'), nullable=False)

    #: the related person (which may have any number of memberships)
    person: 'relationship[Person]' = relationship(
        'Person',
        backref=backref(
            'memberships',
            cascade='all, delete-orphan',
            lazy='dynamic',
        )
    )

    #: the position of the membership within the agency
    order_within_agency = Column(Integer, nullable=False)

    #: the position of the membership within all memberships of a person
    order_within_person = Column(Integer, nullable=False)

    #: describes the membership
    title = Column(Text, nullable=False)

    #: when the membership started
    since = Column(Text, nullable=True)

    # column for full text search index
    fts_idx = Column(TSVECTOR)

    @property
    def search_score(self):
        return 3

    @staticmethod
    def psql_tsvector_string():
        """
        builds the index on column title.
        """
        return Searchable.create_tsvector_string('title')

    @property
    def siblings_by_agency(self):
        """ Returns a query that includes all siblings by agency, including
        the item itself ordered by `order_within_agency`.
        """
        query = object_session(self).query(self.__class__)
        query = query.order_by(self.__class__.order_within_agency)
        query = query.filter(self.__class__.agency == self.agency)
        return query

    @property
    def siblings_by_person(self):
        """ Returns a query that includes all siblings by person, including
        the item itself ordered by `order_within_person`.
        """
        query = object_session(self).query(self.__class__)
        query = query.order_by(self.__class__.order_within_person)
        query = query.filter(self.__class__.person == self.person)
        return query

    def vcard(self, exclude=None):
        """ Returns the person as vCard (3.0).

        Allows to specify the included attributes, provides a reasonable
        default if none are specified. Always includes the first and last
        name.

        """
        if not self.person:
            return ''

        result = self.person.vcard_object(exclude, include_memberships=False)

        line = result.add('org')
        line.value = [f"{self.agency.title}, {self.title}"]
        line.charset_param = 'utf-8'

        return result.serialize()
