from cached_property import cached_property
from onegov.core.layout import ChameleonLayout
from onegov.wtfs import _
from onegov.user import Auth


class DefaultLayout(ChameleonLayout):

    day_long_format = 'skeleton:MMMMd'
    date_long_format = 'long'
    datetime_long_format = 'medium'

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('frameworks')
        self.request.include('chosen')
        self.request.include('common')

    @cached_property
    def title(self):
        return ""

    @cached_property
    def top_navigation(self):
        return []

    @cached_property
    def editbar_links(self):
        return []

    @cached_property
    def breadcrumbs(self):
        return [(_("Homepage"), self.homepage_link, 'current')]

    @cached_property
    def app_version(self):
        return self.app.settings.core.theme.version

    @cached_property
    def static_path(self):
        return self.request.link(self.app.principal, 'static')

    @cached_property
    def homepage_link(self):
        return self.request.link(self.app.principal)

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

    @cached_property
    def sentry_js(self):
        return self.app.sentry_js
