from cached_property import cached_property
from datetime import datetime
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.gazette import _
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import UserGroupCollection
from onegov.gazette.models import Issue
from onegov.gazette.models import Principal
from onegov.gazette.models import UserGroup
from onegov.user import Auth
from onegov.user import UserCollection


class Layout(ChameleonLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('common')
        self.request.include('redactor')
        self.request.include('editor')
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
    def manage_published_notices_link(self):
        return self.request.link(
            GazetteNoticeCollection(self.app.session(), state='published')
        )

    @cached_property
    def dashboard_link(self):
        return self.request.link(self.principal, name='dashboard')

    @cached_property
    def archive_link(self):
        return self.request.link(self.principal, name='archive')

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

        elif self.request.is_private(self.model):
            active = (
                isinstance(self.model, GazetteNoticeCollection) and
                getattr(self.model, 'state', None) == 'submitted'
            )
            result.append((
                _("Submitted Official Notices"), self.manage_notices_link,
                active
            ))

            active = (
                isinstance(self.model, GazetteNoticeCollection) and
                getattr(self.model, 'state', None) == 'published'
            )
            result.append((
                _("Published Official Notices"),
                self.manage_published_notices_link,
                active
            ))

        elif self.request.is_personal(self.model):
            active = (
                isinstance(self.model, Principal) and
                'dashboard' in self.request.url
            )
            result.append((
                _("My Drafted and Submitted Official Notices"),
                self.dashboard_link,
                active
            ))

            active = (
                isinstance(self.model, Principal) and
                'archive' in self.request.url
            )
            result.append((
                _("My Published Official Notices"),
                self.archive_link,
                active
            ))

        return result

    def format_category(self, category):
        return ' / '.join(self.principal.categories_flat.get(category, ['?']))

    def format_issue(self, issue):
        if not isinstance(issue, Issue):
            issue = Issue.from_string(str(issue))

        date_ = self.principal.issues.get(issue.year, {})
        date_ = date_.get(issue.number, None)
        return '?' if not date_ else 'Nr. {}, {}'.format(
            str(issue.number),
            self.format_date(
                self.principal.issues[issue.year][issue.number],
                'date'
            )
        )

    def format_owner(self, owner):
        if owner:
            return owner.realname or owner.username

        return ''

    def format_group(self, user):
        if user:
            group_id = (user.data or {}).get('group')
            if group_id:
                query = self.app.session().query(UserGroup)
                query = query.filter(UserGroup.id == group_id)
                group = query.first()
                if group:
                    return group.name

        return ''


class MailLayout(Layout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def primary_color(self):
        return self.app.theme_options.get('primary-color', '#fff')
