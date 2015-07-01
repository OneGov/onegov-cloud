# -*- coding: utf-8 -*-

from oengov.core.orm.abstract import AdjacencyList
from onegov.core.orm import Base, backref, relationship
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import (
    Column,
    Integer,
    Text,
    Numeric,
    ForeignKey,
    UniqueConstraint
)
from uuid import uuid4


class Organization(AdjacencyList, ContentMixin, TimestampMixin):
    """ Organizations are represented in a hierarchy. Each organization may
    have n suborganizations.

    see :class:`onegov.core.orm.abstract.AdjacencyList`.

    """

    __tablename__ = 'organizations'

    #: the address of the organization, a multiline textfield which will
    #: be parsed for emails and websites
    address = Column(Text, nullable=True)

    #: the point on the globe where this organization is headquartered
    #: for now we assume a single point because we have little need for
    #: complex GIS queries. In the future, we might use PostGIS instead.
    latitude = Column(Numeric(precision=6, asdecimal=True), nullable=True)
    longitude = Column(Numeric(precision=6, asdecimal=True), nullable=True)

    memberships = relationship(
        "Membership",
        cascade="all, delete-orphan",
        backref=backref("organization")
    )


class Person(Base, TimestampMixin):
    """ People are defined singularly and added to zero or more organizations
    through memberships.

    """

    __tablename__ = 'people'

    #: the unique id, part of the url
    id = Column(UUID, primary_key=True, default=uuid4)

    academic_title = Column(Text, nullable=True)

    first_name = Column(Text, nullable=False)

    last_name = Column(Text, nullable=False)

    picture_url = Column(Text, nullable=True)

    email = Column(Text, nullable=True)

    phone = Column(Text, nullable=True)

    website = Column(Text, nullable=True)

    address = Column(Text, nullable=True)

    memberships = relationship(
        "Membership",
        cascade="all, delete-orphan",
        backref=backref("person")
    )


class Membership(Base, TimestampMixin):
    """ Assocation table between people and organizations. Each organizations
    has n people, each person belongs to n organizations.

    Within organizations people may have a specific function.

    """
    __tablename__ = 'memberships'

    id = Column(UUID, primary_key=True, default=uuid4)

    organization_id = Column(
        Integer, ForeignKey(Organization.id), nullable=False)

    person_id = Column(
        UUID, ForeignKey(Person.id), nullable=False)

    function = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('organization_id', 'person_id', name='_org_person'),
    )
