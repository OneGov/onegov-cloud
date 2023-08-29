from datetime import date
from functools import cached_property
from onegov.core.elements import Link
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.wtfs import _
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import NotificationCollection
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import Invoice
from onegov.wtfs.models import Report
from onegov.wtfs.models import UserManual
from onegov.wtfs.security import ViewModel


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.elements import Element
    from onegov.core.request import CoreRequest
    from onegov.wtfs import WtfsApp


class DefaultLayout(ChameleonLayout):

    app: 'WtfsApp'
    day_long_format = 'skeleton:MMMMd'
    date_long_format = 'long'
    datetime_long_format = 'medium'

    def __init__(self, model: object, request: 'CoreRequest'):
        super().__init__(model, request)
        self.request.include('frameworks')
        self.request.include('chosen')
        self.request.include('common')

    @cached_property
    def title(self) -> str:
        return ""

    @cached_property
    def top_navigation(self) -> list['Element']:
        has_permission = self.request.has_permission
        session = self.request.session
        result: list['Element'] = []
        if has_permission(ScanJobCollection(session), ViewModel):
            result.append(Link(_("Scan jobs"), self.scan_jobs_url))
        if has_permission(DailyList(), ViewModel):
            result.append(Link(_("Daily list"), self.daily_list_url))
        if has_permission(Report(session), ViewModel):
            result.append(Link(_("Report"), self.report_url))
        if has_permission(Invoice(session), ViewModel):
            result.append(Link(_("Invoices"), self.invoices_url))
        if has_permission(UserCollection(session), ViewModel):
            result.append(Link(_("Users"), self.users_url))
        if has_permission(MunicipalityCollection(session), ViewModel):
            result.append(Link(_("Municipalities"), self.municipalities_url))
        if has_permission(NotificationCollection(session), ViewModel):
            result.append(Link(_("Notifications"), self.notifications_url))
        if has_permission(UserManual(self.app), ViewModel):
            result.append(Link(_("User manual"), self.user_manual_url))

        return result

    @cached_property
    def editbar_links(self) -> list['Element']:
        return []

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def static_path(self) -> str:
        return self.request.link(self.app.principal, 'static')

    @cached_property
    def sentry_init_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'sentry/js/sentry-init.js'
        )
        return self.request.link(static_file)

    @cached_property
    def homepage_url(self) -> str:
        return self.request.link(self.app.principal)

    def login_to_url(self, to: str | None) -> str:
        return self.request.link(
            Auth.from_request(self.request, to=to),
            name='login'
        )

    @cached_property
    def login_url(self) -> str | None:
        if not self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_url),
                name='login'
            )
        return None

    @cached_property
    def logout_url(self) -> str | None:
        if self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_url),
                name='logout'
            )
        return None

    @cached_property
    def users_url(self) -> str:
        return self.request.link(UserCollection(self.request.session))

    @cached_property
    def municipalities_url(self) -> str:
        return self.request.link(MunicipalityCollection(self.request.session))

    @cached_property
    def scan_jobs_url(self) -> str:
        return self.request.link(ScanJobCollection(self.request.session))

    @cached_property
    def daily_list_url(self) -> str:
        return self.request.link(DailyList())

    @cached_property
    def report_url(self) -> str:
        return self.request.link(Report(self.request.session))

    @cached_property
    def invoices_url(self) -> str:
        return self.request.link(Invoice(self.request.session))

    @cached_property
    def notifications_url(self) -> str:
        return self.request.link(NotificationCollection(self.request.session))

    @cached_property
    def payment_types_url(self) -> str:
        return self.request.link(PaymentTypeCollection(self.request.session))

    @cached_property
    def user_manual_url(self) -> str:
        return self.request.link(UserManual(self.app))

    @cached_property
    def cancel_url(self) -> str:
        return ''

    @cached_property
    def success_url(self) -> str:
        return ''

    @cached_property
    def current_year(self) -> int:
        return date.today().year

    @property
    def notifications(self) -> NotificationCollection:
        return NotificationCollection(self.request.session)
