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


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator
    from onegov.form.parser.core import ParsedField
    from onegov.org.request import OrgRequest


class Organisation(Base, TimestampMixin):
    """ Defines the basic information associated with an organisation.

    It is assumed that there's only one organisation record in the schema!
    """

    __tablename__ = 'organisations'

    #: the id of the organisation, an automatically generated uuid
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the name of the organisation
    name: 'Column[str]' = Column(Text, nullable=False)

    #: the logo of the organisation
    logo_url: 'Column[str | None]' = Column(Text, nullable=True)

    #: the theme options of the organisation
    theme_options: 'Column[dict[str, Any] | None]' = Column(
        JSON,
        nullable=True,
        default=user_options.copy
    )

    #: additional data associated with the organisation
    # FIXME: This should probably not be nullable
    meta: 'Column[dict[str, Any]]' = Column(  # type:ignore[assignment]
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
    analytics_code: dict_property[str | None] = meta_property()
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
    default_map_view: dict_property[str | None] = meta_property()
    homepage_structure: dict_property[str | None] = meta_property()
    homepage_cover: dict_property[str | None] = meta_property()
    square_logo_url: dict_property[str | None] = meta_property()
    locales: dict_property[list[str] | None] = meta_property()
    redirect_homepage_to: dict_property[str | None] = meta_property()
    redirect_path: dict_property[str | None] = meta_property()
    hidden_people_fields: dict_property[list[str]] = meta_property(
        default=list
    )
    event_locations: dict_property[list[str]] = meta_property(default=list)
    geo_provider: dict_property[str] = meta_property(default='geo-mapbox')
    holiday_settings: dict_property[dict[str, Any]] = meta_property(
        default=dict
    )
    hide_onegov_footer: dict_property[bool] = meta_property(default=False)
    standard_image: dict_property[str | None] = meta_property()
    submit_events_visible: dict_property[bool] = meta_property(default=True)
    event_filter_type: dict_property[str] = meta_property(default='tags')
    event_filter_definition: dict_property[str | None] = meta_property()
    event_filter_configuration: dict_property[str | None] = meta_property()

    # social media
    facebook_url: dict_property[str | None] = meta_property()
    twitter_url: dict_property[str | None] = meta_property()
    youtube_url: dict_property[str | None] = meta_property()
    instagram_url: dict_property[str | None] = meta_property()
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
    agency_phone_internal_digits: dict_property[str | None] = meta_property()
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
    logo_in_newsletter: dict_property[bool] = meta_property(default=False)

    # Chat Settings
    chat_staff: dict_property[list[str] | None] = meta_property()
    enable_chat: dict_property[bool] = meta_property(default=False)
    specific_opening_hours: dict_property[bool] = meta_property(default=False)
    opening_hours_chat: dict_property[str | None] = meta_property()

    # Required information to upload documents to a Gever instance
    gever_username: dict_property[str | None] = meta_property()
    gever_password: dict_property[str | None] = meta_property()
    gever_endpoint: dict_property[str | None] = meta_property()

    # data retention policy
    auto_archive_timespan: dict_property[int] = meta_property(default=0)
    auto_delete_timespan: dict_property[int] = meta_property(default=0)

    # MTAN Settings
    mtan_access_window_seconds: dict_property[int | None] = meta_property()
    mtan_access_window_requests: dict_property[int | None] = meta_property()
    mtan_session_duration_seconds: dict_property[int | None] = meta_property()

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
    def school_holidays(self) -> 'Iterator[tuple[date, date]]':
        """ Returns an iterable that yields date pairs of start
        and end dates of school holidays
        """
        for y1, m1, d1, y2, m2, d2 in self.holiday_settings.get('school', ()):
            yield date(y1, m1, d1), date(y2, m2, d2)

    # FIXME: This setter should probably deal with None values
    @contact.setter  # type:ignore[no-redef]
    def contact(self, value: str | None) -> None:
        assert value is not None
        self.meta['contact'] = value
        self.meta['contact_html'] = paragraphify(linkify(value))

    # FIXME: This setter should probably deal with None values
    @opening_hours.setter  # type:ignore[no-redef]
    def opening_hours(self, value: str | None) -> None:
        assert value is not None
        self.meta['opening_hours'] = value
        self.meta['opening_hours_html'] = paragraphify(linkify(value))

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

    def excluded_person_fields(self, request: 'OrgRequest') -> list[str]:
        return [] if request.is_logged_in else self.hidden_people_fields

    @property
    def event_filter_fields(self) -> tuple['ParsedField', ...]:
        return flatten_event_filter_fields_from_definition(
            self.event_filter_definition)


@lru_cache(maxsize=64)
def flatten_event_filter_fields_from_definition(
    definition: str
) -> tuple['ParsedField', ...]:
    return tuple(flatten_fieldsets(parse_formcode(definition)))
