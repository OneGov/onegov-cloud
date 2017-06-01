""" Contains the model describing the organisation proper. """

from onegov.core.orm import Base
from onegov.core.orm.mixins import meta_property, TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.utils import linkify
from onegov.org.theme import user_options
from sqlalchemy import Column, Text
from uuid import uuid4


class Organisation(Base, TimestampMixin):
    """ Defines the basic information associated with an organisation.

    It is assumed that there's only one organisation record in the schema!
    """

    __tablename__ = 'organisations'

    #: the id of the organisation, an automatically generated uuid
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the name of the organisation
    name = Column(Text, nullable=False)

    #: the logo of the organisation
    logo_url = Column(Text, nullable=True)

    #: the theme options of the organisation
    theme_options = Column(JSON, nullable=True, default=user_options.copy)

    #: additional data associated with the organisation
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
    homepage_structure = meta_property('homepage_structure')
    homepage_cover = meta_property('homepage_cover')
    bank_account = meta_property('bank_account')
    bank_beneficiary = meta_property('bank_beneficiary')
    bank_payment_order_type = meta_property('bank_payment_order_type')
    bank_esr_participant_number = meta_property('bank_esr_participant_number')
    square_logo_url = meta_property('square_logo_url')

    @contact.setter
    def contact(self, value):
        self.meta['contact'] = value
        self.meta['contact_html'] = linkify(value).replace('\n', '<br>')

    @opening_hours.setter
    def opening_hours(self, value):
        self.meta['opening_hours'] = value
        self.meta['opening_hours_html'] = linkify(value).replace('\n', '<br>')

    @property
    def title(self):
        return self.name.replace('|', ' ')

    @property
    def title_lines(self):
        if '|' in self.name:
            parts = self.name.split('|')
        else:
            parts = self.name.split(' ')

        return ' '.join(parts[:-1]), parts[-1]
