""" Contains the model describing the organisation proper. """

from onegov.core.orm import Base
from onegov.core.orm.mixins import meta_property, TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.utils import linkify
from onegov.org.theme import user_options
from onegov.org.models.swiss_holidays import SwissHolidays
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
    contact = meta_property()
    contact_url = meta_property()
    opening_hours = meta_property()
    opening_hours_url = meta_property()
    reply_to = meta_property()
    facebook_url = meta_property()
    twitter_url = meta_property()
    analytics_code = meta_property()
    online_counter_label = meta_property()
    reservations_label = meta_property()
    publications_label = meta_property()
    hide_publications = meta_property()
    daypass_label = meta_property()
    default_map_view = meta_property()
    homepage_structure = meta_property()
    homepage_cover = meta_property()
    square_logo_url = meta_property()
    locales = meta_property()
    redirect_homepage_to = meta_property()
    hidden_people_fields = meta_property(default=list)
    event_locations = meta_property(default=list)
    geo_provider = meta_property(default='geo-mapbox')
    holiday_settings = meta_property(default=dict)

    @property
    def holidays(self):
        """ Returns a SwissHolidays instance, as configured by the
        holiday_settings on the UI.

        """
        return SwissHolidays(
            cantons=self.holiday_settings.get('cantons', ()),
            other=self.holiday_settings.get('other', ())
        )

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

    def excluded_person_fields(self, request):
        return [] if request.is_logged_in else self.hidden_people_fields
