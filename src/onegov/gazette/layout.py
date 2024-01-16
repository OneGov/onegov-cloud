from functools import cached_property
from datetime import datetime
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.gazette import _
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.models import Issue
from onegov.gazette.models import OrganizationMove
from onegov.gazette.models import Principal
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from sedate import to_timezone


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from chameleon import BaseTemplate
    from datetime import date
    from onegov.gazette.models import GazetteNotice
    from onegov.gazette.request import GazetteRequest
    from onegov.user import User
    from typing_extensions import TypeAlias

    NestedMenu: TypeAlias = list[tuple[
        str,
        str | None,
        bool,
        'NestedMenu'
    ]]


class Layout(ChameleonLayout):

    request: 'GazetteRequest'

    date_with_weekday_format = 'EEEE dd.MM.yyyy'
    date_long_format = 'd. MMMM yyyy'
    datetime_with_weekday_format = 'EEEE dd.MM.yyyy HH:mm'

    def __init__(self, model: Any, request: 'GazetteRequest') -> None:
        super().__init__(model, request)
        self.request.include('frameworks')
        self.request.include('chosen')
        self.request.include('quill')
        self.request.include('common')
        # FIXME: We don't actually seem to be using any breadcrumbs
        self.breadcrumbs: list[str] = []
        self.session = request.session

    def title(self) -> str:
        return ''

    @cached_property
    def principal(self) -> Principal:
        return self.request.app.principal

    @cached_property
    def user(self) -> 'User | None':
        username = self.request.identity.userid
        if username:
            return UserCollection(
                self.session, username=username
            ).query().first()

        return None

    @cached_property
    def font_awesome_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css'
        )
        return self.request.link(static_file)

    @cached_property
    def sentry_init_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'sentry/js/sentry-init.js'
        )
        return self.request.link(static_file)

    @cached_property
    def copyright_year(self) -> int:
        return datetime.utcnow().year

    @cached_property
    def homepage_link(self) -> str:
        return self.request.link(self.principal)

    @cached_property
    def manage_users_link(self) -> str:
        return self.request.link(UserCollection(self.session))

    @cached_property
    def manage_groups_link(self) -> str:
        return self.request.link(UserGroupCollection(self.session))

    @cached_property
    def manage_organizations_link(self) -> str:
        return self.request.link(OrganizationCollection(self.session))

    @cached_property
    def manage_categories_link(self) -> str:
        return self.request.link(CategoryCollection(self.session))

    @cached_property
    def manage_issues_link(self) -> str:
        return self.request.link(IssueCollection(self.session))

    @cached_property
    def manage_notices_link(self) -> str:
        return self.request.link(
            GazetteNoticeCollection(self.session, state='submitted')
        )

    @cached_property
    def dashboard_link(self) -> str:
        return self.request.link(self.principal, name='dashboard')

    @property
    def dashboard_or_notices_link(self) -> str:
        if self.request.is_secret(self.model):
            return self.manage_notices_link
        return self.dashboard_link

    @cached_property
    def export_users_link(self) -> str:
        return self.request.class_link(UserCollection, name='export')

    @cached_property
    def export_issues_link(self) -> str:
        return self.request.class_link(IssueCollection, name='export')

    @cached_property
    def export_organisation_link(self) -> str:
        return self.request.class_link(OrganizationCollection, name='export')

    @cached_property
    def export_categories_link(self) -> str:
        return self.request.class_link(CategoryCollection, name='export')

    @cached_property
    def login_link(self) -> str | None:
        if self.request.is_logged_in:
            return None

        return self.request.link(
            Auth.from_request(self.request, to=self.homepage_link),
            name='login'
        )

    @cached_property
    def logout_link(self) -> str | None:
        if not self.request.is_logged_in:
            return None

        return self.request.link(
            Auth.from_request(self.request, to=self.homepage_link),
            name='logout'
        )

    @cached_property
    def sortable_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.link(OrganizationMove.for_url_template())
        )

    @cached_property
    def publishing(self) -> bool:
        return self.request.app.principal.publishing

    @cached_property
    def importation(self) -> bool:
        return True if self.request.app.principal.sogc_import else False

    @property
    def menu(self) -> 'NestedMenu':
        result: 'NestedMenu' = []

        if self.request.is_private(self.model):
            # Publisher and Admin
            result.append((
                _("Official Notices"),
                self.manage_notices_link,
                (
                    isinstance(self.model, GazetteNoticeCollection)
                    and 'statistics' not in self.request.url
                ),
                []
            ))

            active = (
                isinstance(self.model, IssueCollection)
                or isinstance(self.model, OrganizationCollection)
                or isinstance(self.model, CategoryCollection)
                or (isinstance(self.model, UserCollection)
                    and 'export' not in self.request.url)
                or isinstance(self.model, UserGroupCollection)
            )
            manage: 'NestedMenu' = [
                (
                    _("Issues"),
                    self.manage_issues_link,
                    isinstance(self.model, IssueCollection),
                    []
                ),
                (
                    _("Organizations"),
                    self.manage_organizations_link,
                    isinstance(self.model, OrganizationCollection),
                    []
                ),
                (
                    _("Categories"),
                    self.manage_categories_link,
                    isinstance(self.model, CategoryCollection),
                    []
                ),
                (
                    _("Groups"),
                    self.manage_groups_link,
                    isinstance(self.model, UserGroupCollection),
                    []
                ),
                (
                    _("Users"),
                    self.manage_users_link,
                    isinstance(self.model, UserCollection),
                    []
                )
            ]
            result.append((_("Manage"), None, active, manage))

            result.append((
                _("Statistics"),
                self.request.link(
                    GazetteNoticeCollection(self.session, state='accepted'),
                    name='statistics'
                ),
                (
                    isinstance(self.model, GazetteNoticeCollection)
                    and 'statistics' in self.request.url
                ),
                []
            ))
            export_links: 'NestedMenu' = [
                (
                    _('Issues'),
                    self.export_issues_link,
                    isinstance(self.model, IssueCollection)
                    and 'export' in self.request.url,
                    []
                ),
                (
                    _('Organizations'),
                    self.export_organisation_link,
                    isinstance(self.model, OrganizationCollection)
                    and 'export' in self.request.url,
                    []
                ),
                (
                    _('Categories'),
                    self.export_categories_link,
                    isinstance(self.model, CategoryCollection)
                    and 'export' in self.request.url,
                    []
                ),
                (
                    _('Users'),
                    self.export_users_link,
                    isinstance(self.model, UserCollection)
                    and 'export' in self.request.url,
                    []
                ),

            ]
            result.append((
                _("Exports"),
                None,
                'export' in self.request.url,
                export_links
            ))

        elif self.request.is_personal(self.model):
            # Editor
            result.append((
                _("Dashboard"),
                self.dashboard_link,
                isinstance(self.model, Principal),
                []
            ))

            result.append((
                _("Published Official Notices"),
                self.request.link(
                    GazetteNoticeCollection(
                        self.session,
                        state='published' if self.publishing else 'accepted'
                    )
                ),
                isinstance(self.model, GazetteNoticeCollection),
                []
            ))

        return result

    @property
    def current_issue(self) -> Issue | None:
        return IssueCollection(self.session).current_issue

    def format_date(self, dt: 'datetime | date | None', format: str) -> str:
        """ Returns a readable version of the given date while automatically
        converting to the principals timezone if the date is timezone aware.

        """
        if getattr(dt, 'tzinfo', None) is not None:
            dt = to_timezone(dt, self.principal.time_zone)  # type:ignore
        return super().format_date(dt, format)

    def format_issue(
        self,
        issue: Issue,
        date_format: str = 'date',
        notice: 'GazetteNotice | None' = None
    ) -> str:
        """ Returns the issues number and date and optionally the publication
        number of the given notice. """

        assert isinstance(issue, Issue)

        issue_number = issue.number or ''
        issue_date = self.format_date(issue.date, date_format)
        notice_number = notice.issues.get(issue.name, None) if notice else None

        if notice_number:
            return self.request.translate(_(
                "No. ${issue_number}, ${issue_date} / ${notice_number}",
                mapping={
                    'issue_number': issue_number,
                    'issue_date': issue_date,
                    'notice_number': notice_number
                }
            ))
        else:
            return self.request.translate(_(
                "No. ${issue_number}, ${issue_date}",
                mapping={
                    'issue_number': issue_number,
                    'issue_date': issue_date
                }
            ))

    def format_text(self, text: str | None) -> str:
        # FIXME: Markupsafe
        return '<br>'.join((text or '').splitlines())


class MailLayout(Layout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self) -> 'BaseTemplate':
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self) -> str:
        return self.app.theme_options.get('primary-color', '#fff')
