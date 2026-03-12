from __future__ import annotations

from functools import cached_property
from onegov.activity import BookingPeriod
from onegov.activity import BookingPeriodMeta
from onegov.activity import BookingPeriodCollection
from onegov.activity import BookingPeriodInvoiceCollection
from onegov.core import utils
from onegov.core.orm import orm_cached
from onegov.feriennet.const import DEFAULT_DONATION_AMOUNTS
from onegov.feriennet.initial_content import create_new_organisation
from onegov.feriennet.request import FeriennetRequest
from onegov.feriennet.sponsors import load_sponsors
from onegov.feriennet.theme import FeriennetTheme
from onegov.org.app import org_content_security_policy
from onegov.town6 import TownApp
from onegov.town6.app import get_common_asset as default_common_asset
from onegov.town6.app import get_i18n_localedirs as get_town6_i18n_localedirs
from onegov.town6.app import (
    get_public_ticket_messages as default_public_ticket_messages)
from onegov.pay.models.invoice_reference import Schema
from onegov.user import User, UserCollection


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from onegov.feriennet.sponsors import Sponsor
    from onegov.org.models import Organisation
    from sqlalchemy.orm import Query
    from uuid import UUID
    from more.content_security import ContentSecurityPolicy


class FeriennetApp(TownApp):

    request_class = FeriennetRequest

    def fts_may_use_private_search(
        self,
        request: FeriennetRequest  # type:ignore[override]
    ) -> bool:
        return request.is_admin

    @orm_cached(policy='on-table-change:periods')
    def active_period(self) -> BookingPeriodMeta | None:
        for period in self.periods:
            if period.active:
                return period
        return None

    @orm_cached(policy='on-table-change:periods')
    def periods(self) -> tuple[BookingPeriodMeta, ...]:
        query: Query[BookingPeriodMeta] = (
            BookingPeriodCollection(self.session())
            .query()
            .order_by(BookingPeriod.execution_start)
            .with_entities(
                BookingPeriod.id,
                BookingPeriod.title,
                BookingPeriod.active,
                BookingPeriod.confirmed,
                BookingPeriod.confirmable,
                BookingPeriod.finalized,
                BookingPeriod.finalizable,
                BookingPeriod.archived,
                BookingPeriod.prebooking_start,
                BookingPeriod.prebooking_end,
                BookingPeriod.booking_start,
                BookingPeriod.booking_end,
                BookingPeriod.execution_start,
                BookingPeriod.execution_end,
                BookingPeriod.max_bookings_per_attendee,
                BookingPeriod.booking_cost,
                BookingPeriod.all_inclusive,
                BookingPeriod.pay_organiser_directly,
                BookingPeriod.minutes_between,
                BookingPeriod.alignment,
                BookingPeriod.deadline_days,
                BookingPeriod.book_finalized,
                BookingPeriod.cancellation_date,
                BookingPeriod.cancellation_days,
                BookingPeriod.age_barrier_type,
            )
        )
        return tuple(BookingPeriodMeta(*row) for row in query)

    @orm_cached(policy='on-table-change:periods')
    def periods_by_id(self) -> dict[str, BookingPeriodMeta]:
        return {
            p.id.hex: p for p in self.periods
        }

    @orm_cached(policy='on-table-change:users')
    def user_titles_by_name(self) -> dict[str, str]:
        return dict(UserCollection(self.session()).query().with_entities(
            User.username, User.title).tuples())

    @orm_cached(policy='on-table-change:users')
    def user_ids_by_name(self) -> dict[str | None, UUID]:
        return dict(UserCollection(self.session()).query().with_entities(
            User.username, User.id).tuples())

    @cached_property
    def sponsors(self) -> list[Sponsor]:
        return load_sponsors(utils.module_path('onegov.feriennet', 'sponsors'))

    def mail_sponsor(self, request: FeriennetRequest) -> list[Sponsor]:
        sponsors = [
            sponsor.compiled(request) for sponsor in self.sponsors
            if getattr(sponsor, 'mail_url', None)
        ]

        if sponsors:
            sponsors[0].banners['narrow'] = sponsors[0].url_for(
                request, sponsors[0].banners['narrow'])

        return sponsors

    @property
    def default_period(self) -> BookingPeriodMeta | None:
        if self.active_period:
            return self.active_period
        return self.periods[0] if self.periods else None

    @property
    def public_organiser_data(self) -> Sequence[str]:
        return self.org.meta.get('public_organiser_data', ('name', 'website'))

    def get_sponsors(
        self,
        request: FeriennetRequest
    ) -> list[Sponsor] | None:

        assert request.locale is not None
        language = request.locale[:2]
        sponsors = [
            sponsor for sponsor in self.sponsors
            if (
                (banners := getattr(sponsor, 'banners', None))
                and banners.get('src', {}).get(language, None)
            )
        ]

        if not sponsors:
            return None
        else:
            return sponsors

    def banners(self, request: FeriennetRequest) -> list[dict[str, str]]:
        sponsors = self.get_sponsors(request)
        banners = []

        for sponsor in sponsors or ():
            sponsor = sponsor.compiled(request)
            info = sponsor.banners.get('info', None)
            banners.append(
                {
                    'src': sponsor.url_for(request, sponsor.banners['src']),
                    'url': sponsor.banners['url'],
                    'info': info if info else ''
                }
            )

        return banners

    def configure_organisation(
        self,
        *,
        enable_user_registration: bool = True,
        enable_yubikey: bool = False,
        disable_password_reset: bool = False,
        **cfg: Any
    ) -> None:
        super().configure_organisation(
            enable_user_registration=enable_user_registration,
            enable_yubikey=enable_yubikey,
            disable_password_reset=disable_password_reset,
            **cfg
        )

    def invoice_schema_config(self) -> tuple[str, dict[str, Any] | None]:
        """ Returns the currently active schema_name and it's config. """
        schema_name: str = self.org.meta.get(
            'bank_reference_schema', 'feriennet-v1')

        if schema_name == 'raiffeisen-v1':
            schema_config = {
                'esr_identification_number': self.org.meta.get(
                    'bank_esr_identification_number'
                )
            }
        else:
            schema_config = None

        return schema_name, schema_config

    def invoice_collection(
        self,
        period_id: UUID | None = None,
        user_id: UUID | None = None
    ) -> BookingPeriodInvoiceCollection:
        """ Returns the invoice collection guaranteed to be configured
        according to the organisation's settings.

        """
        schema_name, schema_config = self.invoice_schema_config()

        return BookingPeriodInvoiceCollection(
            self.session(),
            period_id=period_id,
            user_id=user_id,
            schema=schema_name,
            schema_config=schema_config
        )

    def invoice_bucket(self) -> str:
        """ Returns the active invoice reference bucket. """

        return Schema.render_bucket(*self.invoice_schema_config())

    # FIXME: Are we still using these properties? Because they were broken
    @property
    def show_donate(self) -> bool:
        return self.org.meta.get('donate', True)

    # FIXME: Are we still using these properties? Because they were broken
    @property
    def donation_amounts(self) -> Sequence[int]:
        return self.org.meta.get('donation_amounts', DEFAULT_DONATION_AMOUNTS)

    def show_volunteers(self, request: FeriennetRequest) -> bool:

        if not self.active_period:
            return False

        setting = self.org.meta.get('volunteers', 'disabled')

        if setting == 'enabled':
            return True

        if setting == 'admins' and request.is_admin:
            return True

        return False


@FeriennetApp.template_directory()
def get_template_directory() -> str:
    return 'templates'


@FeriennetApp.setting(section='org', name='create_new_organisation')
def get_create_new_organisation_factory(
) -> Callable[[FeriennetApp, str], Organisation]:
    return create_new_organisation


@FeriennetApp.setting(section='org', name='status_mail_roles')
def get_status_mail_roles() -> Sequence[str]:
    return ('admin', )


@FeriennetApp.setting(section='org', name='ticket_manager_roles')
def get_ticket_manager_roles() -> Sequence[str]:
    return ('admin', )


@FeriennetApp.setting(section='org', name='public_ticket_messages')
def get_public_ticket_messages() -> Sequence[str]:
    return (*default_public_ticket_messages(), 'activity')


@FeriennetApp.setting(section='org', name='require_complete_userprofile')
def get_require_complete_userprofile() -> bool:
    return True


@FeriennetApp.setting(section='org', name='is_complete_userprofile')
def get_is_complete_userprofile_handler(
) -> Callable[[FeriennetRequest, str], bool]:
    from onegov.feriennet.forms import UserProfileForm

    def is_complete_userprofile(
        request: FeriennetRequest,
        username: str,
        user: User | None = None
    ) -> bool:

        user = user or UserCollection(
            request.session).by_username(username)

        form = UserProfileForm()
        form.request = request
        form.model = user
        form.on_request()

        form.process(obj=user)

        for field in form:
            field.raw_data = field.data

        return form.validate()

    return is_complete_userprofile


# NOTE: Feriennet doesn't need a citizen login
@FeriennetApp.setting(section='org', name='citizen_login_enabled')
def get_citizen_login_enabled() -> bool:
    return False


@FeriennetApp.setting(section='i18n', name='localedirs')
def get_i18n_localedirs() -> list[str]:
    return [
        utils.module_path('onegov.feriennet', 'locale'),
        *get_town6_i18n_localedirs()
    ]


@FeriennetApp.setting(section='core', name='theme')
def get_theme() -> FeriennetTheme:
    return FeriennetTheme()


@FeriennetApp.static_directory()
def get_static_directory() -> str:
    return 'static'


@FeriennetApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@FeriennetApp.webasset('volunteer-cart')
def get_volunteer_cart() -> Iterator[str]:
    yield 'volunteer-cart.jsx'


@FeriennetApp.webasset('common')
def get_common_asset() -> Iterator[str]:
    yield from default_common_asset()
    yield 'printthis.js'
    yield 'print.js'
    yield 'click-to-load.js'
    yield 'tracking.js'


@FeriennetApp.setting(section='content_security_policy', name='default')
def feriennet_content_security_policy() -> ContentSecurityPolicy:
    policy = org_content_security_policy()
    policy.connect_src.add('https://*.projuventute.ch')
    policy.connect_src.add('https://*.googletagmanager.com')
    policy.connect_src.add('https://*.analytics.google.com')
    policy.connect_src.add('https://*.google-analytics.com')
    policy.connect_src.add('https://*.usercentrics.eu')
    # NOTE: This one may be out of date, but until somebody complains
    #       we won't worry about it.
    policy.connect_src.add('https://stats.g.doubleclick.net')
    return policy
