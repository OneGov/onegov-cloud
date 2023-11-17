""" Contains the model describing the organisation proper. """

from datetime import date, timedelta
from functools import lru_cache
from hashlib import sha256
from onegov.core.orm import Base
from onegov.core.orm.mixins import dict_property, meta_property, TimestampMixin
from onegov.core.orm.types import JSON, UUID
from onegov.core.utils import linkify, paragraphify
from onegov.form import flatten_fieldsets, parse_formcode
from onegov.org.theme import user_options
from onegov.org.models.tan import DEFAULT_ACCESS_WINDOW
from onegov.org.models.swiss_holidays import SwissHolidays
from sqlalchemy import Column, Text
from uuid import uuid4


from typing import Any


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
    custom_css = meta_property()
    contact = meta_property()
    contact_url = meta_property()
    opening_hours = meta_property()
    opening_hours_url = meta_property()
    about_url = meta_property()
    reply_to = meta_property()
    analytics_code = meta_property()
    online_counter_label = meta_property()
    hide_online_counter = meta_property()
    reservations_label = meta_property()
    hide_reservations = meta_property()
    publications_label = meta_property()
    hide_publications = meta_property()
    event_limit_homepage = meta_property(default=3)
    news_limit_homepage = meta_property(default=2)
    focus_widget_image = meta_property()
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
    hidden_people_fields: dict_property[list[str]] = meta_property(
        default=list
    )
    event_locations: dict_property[list[str]] = meta_property(default=list)
    geo_provider = meta_property(default='geo-mapbox')
    holiday_settings: dict_property[dict[str, Any]] = meta_property(
        default=dict
    )
    hide_onegov_footer = meta_property(default=False)
    standard_image = meta_property()
    submit_events_visible = meta_property(default=True)
    event_filter_type = meta_property(default='tags')
    event_filter_definition = meta_property()
    event_filter_configuration = meta_property()

    # social media
    facebook_url = meta_property()
    twitter_url = meta_property()
    youtube_url = meta_property()
    instagram_url = meta_property()
    og_logo_default = meta_property()

    # custom links
    custom_link_1_name = meta_property()
    custom_link_1_url = meta_property()
    custom_link_2_name = meta_property()
    custom_link_2_url = meta_property()
    custom_link_3_name = meta_property()
    custom_link_3_url = meta_property()

    # partner logos
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
    always_show_partners = meta_property(default=False)

    # Ticket options
    email_for_new_tickets = meta_property()
    ticket_auto_accept_style = meta_property()
    ticket_auto_accepts = meta_property()
    ticket_auto_accept_roles = meta_property()
    tickets_skip_opening_email = meta_property()
    tickets_skip_closing_email = meta_property()
    mute_all_tickets = meta_property()
    ticket_always_notify = meta_property(default=True)
    # username for the user supposed to automatically handle tickets
    auto_closing_user = meta_property()

    # Type boolean
    report_changes = meta_property()

    # PDF rendering options
    pdf_layout = meta_property()
    pdf_link_color = meta_property()
    pdf_underline_links = meta_property(default=False)

    # break points of pages after title of level x, type integer
    page_break_on_level_root_pdf = meta_property()
    page_break_on_level_org_pdf = meta_property()

    # For custom search results or on the people detail view, include topmost
    # n levels as indexes of agency.ancestors, type: list of integers
    agency_display_levels = meta_property()

    # Header settings that go into the div.globals
    header_options: dict_property[dict[str, Any]] = meta_property(default=dict)

    # Setting if show full agency path on people detail view
    agency_path_display_on_people = meta_property(default=False)

    # Setting to index the last digits of the phone number as ES suggestion
    agency_phone_internal_digits = meta_property()
    agency_phone_internal_field = meta_property(default='phone_direct')

    # Favicon urls for favicon macro
    favicon_win_url = meta_property()
    favicon_mac_url = meta_property()
    favicon_apple_touch_url = meta_property()
    favicon_pinned_tab_safari_url = meta_property()

    # Links Settings
    open_files_target_blank = meta_property(default=True)
    disable_page_refs = meta_property(default=True)

    # Footer column width settings
    footer_left_width = meta_property(default=3)
    footer_center_width = meta_property(default=5)
    footer_right_width = meta_property(default=4)

    # Newsletter settings
    show_newsletter = meta_property(default=False)
    logo_in_newsletter = meta_property(default=False)

    # Chat Settings
    chat_staff = meta_property()
    enable_chat = meta_property(default=False)

    # Required information to upload documents to a Gever instance
    gever_username = meta_property()
    gever_password = meta_property()
    gever_endpoint = meta_property()

    # data retention policy
    auto_archive_timespan = meta_property(default=0)
    auto_delete_timespan = meta_property(default=0)

    # MTAN Settings
    mtan_access_window_seconds = meta_property()
    mtan_access_window_requests = meta_property()
    mtan_session_duration_seconds = meta_property()

    @property
    def mtan_access_window(self) -> timedelta:
        seconds = self.mtan_access_window_seconds
        if seconds is None:
            return DEFAULT_ACCESS_WINDOW
        return timedelta(seconds=seconds)

    @property
    def mtan_session_duration(self) -> timedelta:
        seconds = self.mtan_session_duration_seconds
        if seconds is None:
            # by default we match it with the access window
            return self.mtan_access_window
        return timedelta(seconds=seconds)

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

    @property
    def has_school_holidays(self):
        """ Returns whether any school holidays have been configured
        """
        return bool(self.holiday_settings.get('school', ()))

    @property
    def school_holidays(self):
        """ Returns an iterable that yields date pairs of start
        and end dates of school holidays
        """
        for y1, m1, d1, y2, m2, d2 in self.holiday_settings.get('school', ()):
            yield date(y1, m1, d1), date(y2, m2, d2)

    @contact.setter  # type:ignore[no-redef]
    def contact(self, value):
        self.meta['contact'] = value
        self.meta['contact_html'] = paragraphify(linkify(value))

    @opening_hours.setter  # type:ignore[no-redef]
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

    @property
    def event_filter_fields(self):
        return flatten_event_filter_fields_from_definition(
            self.event_filter_definition)


@lru_cache(maxsize=64)
def flatten_event_filter_fields_from_definition(definition):
    return tuple(flatten_fieldsets(parse_formcode(definition)))
