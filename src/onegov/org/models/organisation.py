""" Contains the model describing the organisation proper. """
from __future__ import annotations

from cryptography.fernet import InvalidToken
from datetime import date, timedelta
from functools import cached_property, lru_cache
from hashlib import sha256
from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import (
    dict_markup_property, dict_property, meta_property, TimestampMixin)
from onegov.core.orm.types import JSON, UUID, UTCDateTime
from onegov.core.utils import linkify, paragraphify
from onegov.file.models.file import File
from onegov.form import flatten_fieldsets, parse_formcode
from onegov.org.theme import user_options
from onegov.org.models.tan import DEFAULT_ACCESS_WINDOW
from onegov.org.models.swiss_holidays import SwissHolidays
from sqlalchemy import Column, Text
from uuid import uuid4


from typing import Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator
    from markupsafe import Markup
    from onegov.core.framework import Framework
    from onegov.form.parser.core import ParsedField
    from onegov.org.request import OrgRequest


class KabaConfiguration(NamedTuple):
    site_id: str
    api_key: str
    api_secret: str


class RawKabaConfiguration(NamedTuple):
    site_id: str
    api_key: str
    api_secret: str

    def decrypt(self, app: Framework) -> KabaConfiguration | None:
        try:
            api_secret = app.decrypt(bytes.fromhex(self.api_secret))
        except InvalidToken:
            return None

        return KabaConfiguration(
            site_id=self.site_id,
            api_key=self.api_key,
            api_secret=api_secret
        )


class Organisation(Base, TimestampMixin):
    """ Defines the basic information associated with an organisation.

    It is assumed that there's only one organisation record in the schema!
    """

    __tablename__ = 'organisations'

    #: the id of the organisation, an automatically generated uuid
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name of the organisation
    name: Column[str] = Column(Text, nullable=False)

    #: the logo of the organisation
    logo_url: Column[str | None] = Column(Text, nullable=True)

    #: the theme options of the organisation
    theme_options: Column[dict[str, Any] | None] = Column(
        JSON,
        nullable=True,
        default=user_options.copy
    )

    #: additional data associated with the organisation
    # FIXME: This should probably not be nullable
    meta: Column[dict[str, Any]] = Column(  # type:ignore[assignment]
        JSON,
        nullable=True,
        default=dict
    )

    # meta bound values
    custom_css: dict_property[str | None] = meta_property()
    contact: dict_property[str | None] = meta_property()
    contact_url: dict_property[str | None] = meta_property()
    opening_hours: dict_property[str | None] = meta_property()
    opening_hours_url: dict_property[str | None] = meta_property()
    about_url: dict_property[str | None] = meta_property()
    reply_to: dict_property[str | None] = meta_property()
    # FIXME: This is inherently unsafe, we should consider hard-coding
    #        support for the few providers we need instead and only
    #        allow users to select a provider and set the token(s)
    #        and other configuration options available to that provider
    analytics_code = dict_markup_property('meta')
    online_counter_label: dict_property[str | None] = meta_property()
    hide_online_counter: dict_property[bool | None] = meta_property()
    reservations_label: dict_property[str | None] = meta_property()
    hide_reservations: dict_property[bool | None] = meta_property()
    publications_label: dict_property[str | None] = meta_property()
    hide_publications: dict_property[bool | None] = meta_property()
    event_limit_homepage: dict_property[int] = meta_property(default=3)
    news_limit_homepage: dict_property[int] = meta_property(default=2)
    focus_widget_image: dict_property[str | None] = meta_property()
    daypass_label: dict_property[str | None] = meta_property()
    e_move_label: dict_property[str | None] = meta_property()
    e_move_url: dict_property[str | None] = meta_property()
    default_map_view: dict_property[dict[str, Any] | None] = meta_property()
    homepage_structure: dict_property[str | None] = meta_property()
    homepage_cover = dict_markup_property('meta')
    square_logo_url: dict_property[str | None] = meta_property()
    # FIXME: really not a great name for this property considering
    #        this is a single selection...
    locales: dict_property[str | None] = meta_property()
    redirect_homepage_to: dict_property[str | None] = meta_property()
    redirect_path: dict_property[str | None] = meta_property()
    hidden_people_fields: dict_property[list[str]] = meta_property(
        default=lambda: ['external_user_id']
    )
    event_locations: dict_property[list[str]] = meta_property(default=list)
    geo_provider: dict_property[str] = meta_property(default='geo-mapbox')
    holiday_settings: dict_property[dict[str, Any]] = meta_property(
        default=dict
    )
    hide_onegov_footer: dict_property[bool] = meta_property(default=False)
    standard_image: dict_property[str | None] = meta_property()
    submit_events_visible: dict_property[bool] = meta_property(default=True)
    delete_past_events: dict_property[bool] = meta_property(default=False)
    event_filter_type: dict_property[str] = meta_property(default='tags')
    event_filter_definition: dict_property[str | None] = meta_property()
    event_filter_configuration: dict_property[dict[str, Any]]
    event_filter_configuration = meta_property(default=dict)
    event_header_html: dict_markup_property[Markup | None]
    event_header_html = dict_markup_property('meta')
    event_footer_html: dict_markup_property[Markup | None]
    event_footer_html = dict_markup_property('meta')
    event_files = associated(File, 'event_files', 'many-to-many')

    # social media
    facebook_url: dict_property[str | None] = meta_property()
    twitter_url: dict_property[str | None] = meta_property()
    youtube_url: dict_property[str | None] = meta_property()
    instagram_url: dict_property[str | None] = meta_property()
    linkedin_url: dict_property[str | None] = meta_property()
    tiktok_url: dict_property[str | None] = meta_property()
    og_logo_default: dict_property[str | None] = meta_property()

    # custom links
    custom_link_1_name: dict_property[str | None] = meta_property()
    custom_link_1_url: dict_property[str | None] = meta_property()
    custom_link_2_name: dict_property[str | None] = meta_property()
    custom_link_2_url: dict_property[str | None] = meta_property()
    custom_link_3_name: dict_property[str | None] = meta_property()
    custom_link_3_url: dict_property[str | None] = meta_property()

    # partner logos
    partner_1_img: dict_property[str | None] = meta_property()
    partner_1_url: dict_property[str | None] = meta_property()
    partner_1_name: dict_property[str | None] = meta_property()

    partner_2_img: dict_property[str | None] = meta_property()
    partner_2_url: dict_property[str | None] = meta_property()
    partner_2_name: dict_property[str | None] = meta_property()

    partner_3_img: dict_property[str | None] = meta_property()
    partner_3_url: dict_property[str | None] = meta_property()
    partner_3_name: dict_property[str | None] = meta_property()

    partner_4_img: dict_property[str | None] = meta_property()
    partner_4_url: dict_property[str | None] = meta_property()
    partner_4_name: dict_property[str | None] = meta_property()
    always_show_partners: dict_property[bool] = meta_property(default=False)

    # Ticket options
    ticket_tags: dict_property[list[str | dict[str, dict[str, Any]]]]
    ticket_tags = meta_property(default=list)
    hide_personal_email: dict_property[bool] = meta_property(default=False)
    general_email: dict_property[str | None] = meta_property()
    email_for_new_tickets: dict_property[str | None] = meta_property()
    ticket_auto_accept_style: dict_property[str | None] = meta_property()
    ticket_auto_accepts: dict_property[list[str] | None] = meta_property()
    ticket_auto_accept_roles: dict_property[list[str] | None] = meta_property()
    tickets_skip_opening_email: dict_property[list[str] | None]
    tickets_skip_opening_email = meta_property()
    tickets_skip_closing_email: dict_property[list[str] | None]
    tickets_skip_closing_email = meta_property()
    mute_all_tickets: dict_property[bool | None] = meta_property()
    ticket_always_notify: dict_property[bool] = meta_property(default=True)
    # username for the user supposed to automatically handle tickets
    auto_closing_user: dict_property[str | None] = meta_property()

    # Type boolean
    report_changes: dict_property[bool | None] = meta_property()

    # PDF rendering options
    pdf_layout: dict_property[str | None] = meta_property()
    pdf_link_color: dict_property[str | None] = meta_property()
    pdf_underline_links: dict_property[bool] = meta_property(default=False)

    # break points of pages after title of level x, type integer
    page_break_on_level_root_pdf: dict_property[int | None] = meta_property()
    page_break_on_level_org_pdf: dict_property[int | None] = meta_property()

    # For custom search results or on the people detail view, include topmost
    # n levels as indexes of agency.ancestors, type: list of integers
    agency_display_levels: dict_property[list[int] | None] = meta_property()

    # Header settings that go into the div.globals
    header_options: dict_property[dict[str, Any]] = meta_property(default=dict)

    # Setting if show full agency path on people detail view
    agency_path_display_on_people: dict_property[bool]
    agency_path_display_on_people = meta_property(default=False)

    # Setting to index the last digits of the phone number as ES suggestion
    agency_phone_internal_digits: dict_property[int | None] = meta_property()
    agency_phone_internal_field: dict_property[str]
    agency_phone_internal_field = meta_property(default='phone_direct')

    # Favicon urls for favicon macro
    favicon_win_url: dict_property[str | None] = meta_property()
    favicon_mac_url: dict_property[str | None] = meta_property()
    favicon_apple_touch_url: dict_property[str | None] = meta_property()
    favicon_pinned_tab_safari_url: dict_property[str | None] = meta_property()

    # Links Settings
    open_files_target_blank: dict_property[bool] = meta_property(default=True)
    disable_page_refs: dict_property[bool] = meta_property(default=True)

    # Footer column width settings
    footer_left_width: dict_property[int] = meta_property(default=3)
    footer_center_width: dict_property[int] = meta_property(default=5)
    footer_right_width: dict_property[int] = meta_property(default=4)

    # Newsletter settings
    show_newsletter: dict_property[bool] = meta_property(default=False)
    secret_content_allowed: dict_property[bool] = meta_property(default=False)
    newsletter_categories: dict_property[list[dict[str, list[str]] | str]] = (
        meta_property(default=list)
    )
    notify_on_unsubscription: dict_property[list[str] | None] = meta_property()
    enable_automatic_newsletters: dict_property[bool] = meta_property(
        default=False)
    newsletter_times: dict_property[list[str] | None] = meta_property()

    # Chat Settings
    chat_staff: dict_property[list[str] | None] = meta_property()
    enable_chat: dict_property[bool] = meta_property(default=False)
    specific_opening_hours: dict_property[bool] = meta_property(default=False)
    opening_hours_chat: dict_property[list[list[str]] | None] = meta_property()
    chat_topics: dict_property[list[str] | None] = meta_property()

    # People Settings
    organisation_hierarchy: dict_property[list[dict[str, list[str]] | str]] = (
        meta_property(default=list)
    )

    # Required information to upload documents to a Gever instance
    gever_username: dict_property[str | None] = meta_property()
    gever_password: dict_property[str | None] = meta_property()
    gever_endpoint: dict_property[str | None] = meta_property()

    # Kaba settings
    @property
    def kaba_configurations(self) -> list[RawKabaConfiguration]:
        return [
            RawKabaConfiguration(**config)
            for config in self.meta.get('kaba_configurations', ())
        ]

    def get_kaba_configuration(
        self,
        site_id: str
    ) -> RawKabaConfiguration | None:
        for config in self.meta.get('kaba_configurations', ()):
            if config.get('site_id') == site_id:
                return RawKabaConfiguration(**config)
        return None

    default_key_code_lead_time: dict_property[int] = meta_property(default=30)
    default_key_code_lag_time: dict_property[int] = meta_property(default=30)

    # data retention policy
    auto_archive_timespan: dict_property[int] = meta_property(default=0)
    auto_delete_timespan: dict_property[int] = meta_property(default=0)

    # vat
    vat_rate: dict_property[float | None] = meta_property(default=0.0)

    # RIS settings
    ris_enabled: dict_property[bool] = meta_property(default=False)

    # MTAN Settings
    mtan_access_window_seconds: dict_property[int | None] = meta_property()
    mtan_access_window_requests: dict_property[int | None] = meta_property()
    mtan_session_duration_seconds: dict_property[int | None] = meta_property()

    # Citizen Login
    citizen_login_enabled: dict_property[bool] = meta_property(default=False)

    # Open Data
    ogd_publisher_mail: dict_property[str | None] = meta_property()
    ogd_publisher_id: dict_property[str | None] = meta_property()
    ogd_publisher_name: dict_property[str | None] = meta_property()

    # cron jobs
    hourly_maintenance_tasks_last_run: (
        dict_property)[UTCDateTime | None] = (meta_property(default=None))

    firebase_adminsdk_credential: dict_property[str | None] = meta_property()
    selectable_push_notification_options: dict_property[list[list[str]]] = (
        meta_property(default=list)
    )

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
    def public_identity(self) -> str:
        """ The public identity is a globally unique SHA 256 hash of the
        current organisation.

        Basically, this is the database record of the database, but mangled
        for security and because it is cooler 😎.

        This value can be accessed through /identity.

        """
        return sha256(self.id.hex.encode('utf-8')).hexdigest()

    @property
    def holidays(self) -> SwissHolidays:
        """ Returns a SwissHolidays instance, as configured by the
        holiday_settings on the UI.

        """
        return SwissHolidays(
            cantons=self.holiday_settings.get('cantons', ()),
            other=self.holiday_settings.get('other', ())
        )

    @property
    def has_school_holidays(self) -> bool:
        """ Returns whether any school holidays have been configured
        """
        return bool(self.holiday_settings.get('school', ()))

    @property
    def school_holidays(self) -> Iterator[tuple[date, date]]:
        """ Returns an iterable that yields date pairs of start
        and end dates of school holidays
        """
        for y1, m1, d1, y2, m2, d2 in self.holiday_settings.get('school', ()):
            yield date(y1, m1, d1), date(y2, m2, d2)

    @contact.setter  # type:ignore[no-redef]
    def contact(self, value: str | None) -> None:
        self.meta['contact'] = value
        # update cache
        self.__dict__['contact_html'] = paragraphify(linkify(value))

    @cached_property
    def contact_html(self) -> Markup:
        return paragraphify(linkify(self.contact))

    @opening_hours.setter  # type:ignore[no-redef]
    def opening_hours(self, value: str | None) -> None:
        self.meta['opening_hours'] = value
        # update cache
        self.__dict__['opening_hours_html'] = paragraphify(linkify(value))

    @cached_property
    def opening_hours_html(self) -> Markup:
        return paragraphify(linkify(self.opening_hours))

    @property
    def title(self) -> str:
        return self.name.replace('|', ' ')

    @property
    def title_lines(self) -> tuple[str, str]:
        if '|' in self.name:
            parts = self.name.split('|')
        else:
            parts = self.name.split(' ')

        return ' '.join(parts[:-1]), parts[-1]

    def excluded_person_fields(self, request: OrgRequest) -> list[str]:
        return [] if request.is_logged_in else self.hidden_people_fields

    @property
    def event_filter_fields(self) -> tuple[ParsedField, ...]:
        return flatten_event_filter_fields_from_definition(
            self.event_filter_definition)


@lru_cache(maxsize=64)
def flatten_event_filter_fields_from_definition(
    definition: str | None
) -> tuple[ParsedField, ...]:
    if not definition:
        return ()
    return tuple(flatten_fieldsets(parse_formcode(definition)))
