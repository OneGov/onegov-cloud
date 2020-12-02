""" Contains the model describing the organisation proper. """

from hashlib import sha256
from onegov.core.orm import Base
from onegov.core.orm.mixins import meta_property, TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.utils import linkify, paragraphify
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
    about_url = meta_property()
    reply_to = meta_property()
    analytics_code = meta_property()
    online_counter_label = meta_property()
    reservations_label = meta_property()
    publications_label = meta_property()
    hide_publications = meta_property()
    daypass_label = meta_property()
    e_move_label = meta_property()
    e_move_url = meta_property()
    default_map_view = meta_property()
    homepage_structure = meta_property()
    homepage_cover = meta_property()
    square_logo_url = meta_property()
    locales = meta_property()
    redirect_homepage_to = meta_property()
    redirect_path = meta_property()
    hidden_people_fields = meta_property(default=list)
    event_locations = meta_property(default=list)
    geo_provider = meta_property(default='geo-mapbox')
    holiday_settings = meta_property(default=dict)
    hide_onegov_footer = meta_property(default=False)

    # social media
    facebook_url = meta_property()
    twitter_url = meta_property()
    youtube_url = meta_property()
    instagram_url = meta_property()

    # custom links
    custom_link_1_name = meta_property()
    custom_link_1_url = meta_property()
    custom_link_2_name = meta_property()
    custom_link_2_url = meta_property()
    custom_link_3_name = meta_property()
    custom_link_3_url = meta_property()

    # parter logos
    partner_1_img = meta_property()
    partner_1_url = meta_property()
    partner_1_name = meta_property()

    partner_2_img = meta_property()
    partner_2_url = meta_property()
    partner_2_name = meta_property()

    partner_3_img = meta_property()
    partner_3_url = meta_property()
    partner_3_name = meta_property()

    partner_4_img = meta_property()
    partner_4_url = meta_property()
    partner_4_name = meta_property()

    # Ticket options
    ticket_auto_accepts = meta_property()
    tickets_skip_opening_email = meta_property()
    mute_all_tickets = meta_property()

    # Type boolean
    report_changes = meta_property()

    # PDF rendering options
    pdf_layout = meta_property()

    # break points of pages after title of level x, type integer
    page_break_on_level_root_pdf = meta_property()
    page_break_on_level_org_pdf = meta_property()

    # For custom search results or on the people detail view, include topmost
    # n levels as indexes of agency.ancestors, type: list of integers
    agency_display_levels = meta_property()

    # Header settings that go into the div.globals
    header_options = meta_property(default=dict)

    # Setting if show full agency path on people detail view
    agency_path_display_on_people = meta_property(default=False)

    @property
    def public_identity(self):
        """ The public identity is a globally unique SHA 256 hash of the
        current organisation.

        Basically, this is the database record of the database, but mangled
        for security and because it is cooler 😎.

        This value can be accessed through /identity.

        """
        return sha256(self.id.hex.encode('utf-8')).hexdigest()

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
        self.meta['contact_html'] = paragraphify(linkify(value))

    @opening_hours.setter
    def opening_hours(self, value):
        self.meta['opening_hours'] = value
        self.meta['opening_hours_html'] = paragraphify(linkify(value))

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
