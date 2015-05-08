""" Contains the model describing the town proper. """

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.town.theme import user_options
from sqlalchemy import Column, Text
from uuid import uuid4


class Town(Base, TimestampMixin):
    """ Defines the basic information associated with a town.

    It is assumed that there's only one town record in the schema associated
    with this town.
    """

    __tablename__ = 'towns'

    #: the id of the town, an automatically generated uuid
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the name of the town (as registered with the Swiss governement)
    name = Column(Text, nullable=False)

    #: the logo of the town
    logo_url = Column(Text, nullable=True)

    #: the theme options of the town
    theme_options = Column(JSON, nullable=True, default=user_options.copy)

    #: additional data associated with the town
    meta = Column(JSON, nullable=True, default=dict)
