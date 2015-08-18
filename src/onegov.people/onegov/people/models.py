# -*- coding: utf-8 -*-

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column, Text
from uuid import uuid4


class Person(Base, TimestampMixin):

    __tablename__ = 'people'

    @property
    def title(self):
        if self.salutation:
            parts = self.salutation, self.first_name, self.last_name
        else:
            parts = self.first_name, self.last_name

        return u" ".join(parts)

    #: the unique id, part of the url
    id = Column(UUID, primary_key=True, default=uuid4)

    salutation = Column(Text, nullable=True)

    first_name = Column(Text, nullable=False)

    last_name = Column(Text, nullable=False)

    picture_url = Column(Text, nullable=True)

    email = Column(Text, nullable=True)

    phone = Column(Text, nullable=True)

    website = Column(Text, nullable=True)

    address = Column(Text, nullable=True)
