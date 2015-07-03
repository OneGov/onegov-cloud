# -*- coding: utf-8 -*-

from hashlib import md5
from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import (
    Column,
    Text
)
from sqlalchemy.orm import backref, relationship
from uuid import uuid4


class Person(Base, TimestampMixin):

    __tablename__ = 'people'

    @property
    def title(self):
        if self.academic_title:
            return u" ".join(
                (self.academic_title, self.first_name, self.last_name))
        else:
            return u" ".join((self.first_name, self.last_name))

    @property
    def gravatar_url(self):
        if self.email:
            return 'https://www.gravatar.com/avatar/{}?s=200'.format(
                md5(self.email.encode('utf-8')).hexdigest()
            )

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
