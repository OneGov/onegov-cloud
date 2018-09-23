from babel import Locale
from cached_property import cached_property
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.user import Auth


class DefaultLayout(ChameleonLayout):

    day_long_format = 'skeleton:MMMMd'
    date_long_format = 'long'
    datetime_long_format = 'medium'

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('common')

        self.pages = TranslatablePageCollection(self.request.session)

    @cached_property
    def title(self):
        return ""

    @cached_property
    def top_navigation(self):
        result = [(_("Votes"), self.votes_link)]

        for page in ('dataset', 'about', 'contact'):
            page = self.pages.by_id(page)
            result.append((page.title, self.request.link(page)))

        return result

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
    def disclaimer_link(self):
        page = self.pages.by_id('disclaimer')
        return page.title, self.request.link(page)

    @cached_property
    def imprint_link(self):
        page = self.pages.by_id('imprint')
        return page.title, self.request.link(page)

    @cached_property
    def votes_link(self):
        return self.request.link(SwissVoteCollection(self.app))

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
    def locales(self):
        result = []
        assert self.app.locales == {'de_CH', 'fr_CH', 'en_US'}
        for locale_code in ('de_CH', 'fr_CH', 'en_US'):
            locale = Locale.parse(locale_code)
            result.append((
                locale_code,
                locale.language,
                locale.get_language_name().capitalize(),
                self.request.link(SiteLocale(locale_code, self.request.url))
            ))
        return result

    @cached_property
    def sentry_js(self):
        return self.app.sentry_js
