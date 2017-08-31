from cached_property import cached_property
from datetime import datetime
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.gazette import _
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.models import Issue
from onegov.gazette.models import Principal
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.user import UserGroupCollection


class Layout(ChameleonLayout):

    date_with_weekday_format = 'EEEE dd.MM.yyyy'
    datetime_with_weekday_format = 'EEEE dd.MM.yyyy HH:mm'

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('frameworks')
        self.request.include('quill')
        self.request.include('common')
        self.breadcrumbs = []

    def title(self):
        return ''

    @cached_property
    def app_version(self):
        return self.app.settings.core.theme.version

    @cached_property
    def principal(self):
        return self.request.app.principal

    @cached_property
    def user(self):
        username = self.request.identity.userid
        if username:
            return UserCollection(
                self.app.session(), username=username
            ).query().first()

        return None

    @cached_property
    def font_awesome_path(self):
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css'
        )
        return self.request.link(static_file)

    @cached_property
    def copyright_year(self):
        return datetime.utcnow().year

    @cached_property
    def sentry_js(self):
        return self.app.sentry_js

    @cached_property
    def homepage_link(self):
        return self.request.link(self.principal)

    @cached_property
    def manage_link(self):
        return self.request.link(self.principal)

    @cached_property
    def manage_users_link(self):
        return self.request.link(UserCollection(self.app.session()))

    @cached_property
    def manage_user_groups_link(self):
        return self.request.link(UserGroupCollection(self.app.session()))

    @cached_property
    def manage_notices_link(self):
        return self.request.link(
            GazetteNoticeCollection(self.app.session(), state='submitted')
        )

    @cached_property
    def manage_accepted_notices_link(self):
        return self.request.link(
            GazetteNoticeCollection(self.app.session(), state='accepted')
        )

    @cached_property
    def manage_statistics_link(self):
        return self.request.link(
            GazetteNoticeCollection(self.app.session(), state='accepted'),
            name='statistics'
        )

    @cached_property
    def dashboard_link(self):
        return self.request.link(self.principal, name='dashboard')

    @cached_property
    def login_link(self):
        if not self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_link),
                name='login'
            )

    @cached_property
    def logout_link(self):
        if self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_link),
                name='logout'
            )

    @property
    def menu(self):
        result = []
        if self.request.is_secret(self.model):
            active = isinstance(self.model, UserCollection)
            result.append((
                _("Users"), self.manage_users_link, active
            ))

            active = isinstance(self.model, UserGroupCollection)
            result.append((
                _("Groups"), self.manage_user_groups_link, active
            ))

        if self.request.is_private(self.model):
            active = (
                isinstance(self.model, GazetteNoticeCollection) and
                'statistics' not in self.request.url
            )
            result.append((
                _("Official Notices"), self.manage_notices_link,
                active
            ))

            active = (
                isinstance(self.model, GazetteNoticeCollection) and
                'statistics' in self.request.url
            )
            result.append((
                _("Statistics"),
                self.manage_statistics_link,
                active
            ))

        elif self.request.is_personal(self.model):
            active = isinstance(self.model, Principal)
            result.append((
                _("My Drafted and Submitted Official Notices"),
                self.dashboard_link,
                active
            ))

            active = isinstance(self.model, GazetteNoticeCollection)
            result.append((
                _("My Accepted Official Notices"),
                self.manage_accepted_notices_link,
                active
            ))

        return result

    def format_issue(self, issue, date_format='date'):
        if not isinstance(issue, Issue):
            issue = Issue.from_string(str(issue))

        dates = self.principal.issue(issue)
        if dates:
            return self.request.translate(_(
                "No. ${number}, ${issue_date}",
                mapping={
                    'number': issue.number,
                    'issue_date': self.format_date(
                        dates.issue_date, date_format
                    )
                }
            ))

        return '?'

    def format_deadline(self, issue, date_format='datetime_with_weekday'):
        if not isinstance(issue, Issue):
            issue = Issue.from_string(str(issue))

        dates = self.principal.issue(issue)
        if dates:
            return self.format_date(dates.deadline, date_format)

        return '?'


class MailLayout(Layout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self):
        return self.app.theme_options.get('primary-color', '#fff')
