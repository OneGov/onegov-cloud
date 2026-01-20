from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.mixins import UTCPublicationMixin
from onegov.core.orm.types import UUID
from onegov.search import ORMSearchable
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from translationstring import TranslationString
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Collection
    from sqlalchemy.orm import Query
    from typing import Self
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
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    # HACK: We don't want to set up translations in this module for this single
    #       string, we know we already have a translation in a different domain
    #       so we just manually specify it for now.
    fts_type_title = TranslationString('Memberships', domain='onegov.agency')
    fts_public = True
    fts_title_property = 'title'
    fts_properties = {
        'title': {'type': 'localized', 'weight': 'A'},
    }

    #: the unique id, part of the url
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the id of the agency
    agency_id: Column[int] = Column(
        Integer,
        ForeignKey('agencies.id'),
        nullable=False
    )

    #: the related agency (which may have any number of memberships)
    agency: relationship[Agency] = relationship(
        'Agency',
        back_populates='memberships'
    )

    #: the id of the person
    person_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('people.id'),
        nullable=False
    )

    #: the related person (which may have any number of memberships)
    person: relationship[Person] = relationship(
        'Person',
        back_populates='memberships',
    )

    #: the position of the membership within the agency
    order_within_agency: Column[int] = Column(Integer, nullable=False)

    #: the position of the membership within all memberships of a person
    order_within_person: Column[int] = Column(Integer, nullable=False)

    #: describes the membership
    title: Column[str] = Column(Text, nullable=False)

    #: when the membership started
    since: Column[str | None] = Column(Text, nullable=True)

    @property
    def siblings_by_agency(self) -> Query[Self]:
        """ Returns a query that includes all siblings by agency, including
        the item itself ordered by `order_within_agency`.
        """
        # FIXME: This has the same problem as AdjacencyList.siblings
        cls = self.__class__
        query = object_session(self).query(cls)
        query = query.order_by(cls.order_within_agency)
        query = query.filter(cls.agency == self.agency)
        return query

    @property
    def siblings_by_person(self) -> Query[Self]:
        """ Returns a query that includes all siblings by person, including
        the item itself ordered by `order_within_person`.
        """
        # FIXME: This has the same problem as AdjacencyList.siblings
        cls = self.__class__
        query = object_session(self).query(cls)
        query = query.order_by(cls.order_within_person)
        query = query.filter(cls.person == self.person)
        return query

    def vcard(self, exclude: Collection[str] | None = None) -> str:
        """ Returns the person as vCard (3.0).

        Allows to specify the included attributes, provides a reasonable
        default if none are specified. Always includes the first and last
        name.

        """
        if not self.person:
            return ''

        result = self.person.vcard_object(exclude, include_memberships=False)

        line = result.add('org')
        line.value = [f'{self.agency.title}, {self.title}']
        line.charset_param = 'utf-8'

        return result.serialize()
