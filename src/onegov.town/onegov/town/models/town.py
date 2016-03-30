""" Contains the model describing the town proper. """

from onegov.core.orm import Base
from onegov.core.orm.mixins import meta_property, TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.utils import linkify
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

    # meta bound values
    contact = meta_property('contact')
    contact_url = meta_property('contact_url')
    opening_hours = meta_property('opening_hours')
    opening_hours_url = meta_property('opening_hours_url')
    reply_to = meta_property('reply_to')
    facebook_url = meta_property('facebook_url')
    twitter_url = meta_property('twitter_url')
    analytics_code = meta_property('analytics_code')
    online_counter_label = meta_property('online_counter_label')
    reservations_label = meta_property('reservations_label')
    daypass_label = meta_property('daypass_label')
    default_map_view = meta_property('default_map_view')

    @contact.setter
    def contact(self, value):
        self.meta['contact'] = value
        self.meta['contact_html'] = linkify(value).replace('\n', '<br>')

    @opening_hours.setter
    def opening_hours(self, value):
        self.meta['opening_hours'] = value
        self.meta['opening_hours_html'] = linkify(value).replace('\n', '<br>')
