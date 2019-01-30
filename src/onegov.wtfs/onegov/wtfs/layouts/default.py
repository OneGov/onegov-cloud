from cached_property import cached_property
from onegov.core.elements import Link
from onegov.core.layout import ChameleonLayout
from onegov.user import Auth
from onegov.wtfs import _
from onegov.wtfs.collections import MunicipalityCollection


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
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def app_version(self):
        return self.app.settings.core.theme.version

    @cached_property
    def static_path(self):
        return self.request.link(self.app.principal, 'static')

    @cached_property
    def homepage_url(self):
        return self.request.link(self.app.principal)

    @cached_property
    def login_url(self):
        if not self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_url),
                name='login'
            )

    @cached_property
    def logout_url(self):
        if self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.homepage_url),
                name='logout'
            )

    @cached_property
    def municipalities_url(self):
        return self.request.link(MunicipalityCollection(self.request.session))

    @cached_property
    def cancel_url(self):
        return ''

    @cached_property
    def success_url(self):
        return ''

    @cached_property
    def sentry_js(self):
        return self.app.sentry_js
