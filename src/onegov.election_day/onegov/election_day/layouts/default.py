from babel import Locale
from cached_property import cached_property
from datetime import datetime
from onegov.ballot import VoteCollection
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.election_day import _
from onegov.election_day.collections import ArchivedResultCollection
from onegov.user import Auth


class DefaultLayout(ChameleonLayout):

    day_long_format = 'skeleton:MMMMd'
    date_long_format = 'long'
    datetime_long_format = 'medium'

    def __init__(self, model, request):
        super().__init__(model, request)

        self.request.include('common')
        self.request.include('custom')

        if 'headerless' in request.params:
            request.browser_session['headerless'] = True
        if 'headerful' in request.params:
            if request.browser_session.has('headerless'):
                del request.browser_session['headerless']

    def title(self):
        return ''

    @cached_property
    def app_version(self):
        return self.app.settings.core.theme.version

    @cached_property
    def principal(self):
        return self.request.app.principal

    @cached_property
    def homepage_link(self):
        return self.request.link(self.principal)

    def get_opendata_link(self, lang):
        return (
            "https://github.com/OneGov/onegov.election_day"
            "/blob/master/docs/open_data_{}.md"
        ).format(lang)

    @cached_property
    def opendata_link(self):
        lang = (self.request.locale or 'en')[:2]
        return self.get_opendata_link(lang)

    @cached_property
    def terms_icon(self):
        static_file = StaticFile.from_application(
            self.app, 'images/terms_by.svg'
        )

        return self.request.link(static_file)

    @cached_property
    def terms_link(self):
        lang = (self.request.locale or 'en')[:2]
        return "https://opendata.swiss/{}/terms-of-use".format(lang)

    @cached_property
    def format_description_link(self):
        lang = (self.request.locale or 'en')[:2]
        return (
            "https://github.com/OneGov/onegov.election_day"
            "/blob/master/docs/format__{}.md"
        ).format(lang)

    @cached_property
    def font_awesome_path(self):
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css')

        return self.request.link(static_file)

    def get_topojson_link(self, id, year):
        return self.request.link(
            StaticFile('mapdata/{}/{}.json'.format(year, id))
        )

    @cached_property
    def copyright_year(self):
        return datetime.utcnow().year

    @cached_property
    def manage_link(self):
        return self.request.link(VoteCollection(self.app.session()))

    @cached_property
    def login_link(self):
        if not self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request, to=self.manage_link),
                name='login'
            )

    @cached_property
    def logout_link(self):
        if self.request.is_logged_in:
            return self.request.link(
                Auth.from_request(self.request), name='logout')

    @cached_property
    def archive(self):
        return ArchivedResultCollection(self.request.session)

    @cached_property
    def locales(self):
        to = self.request.url

        def get_name(locale):
            return Locale.parse(locale).get_language_name().capitalize()

        def get_link(locale):
            return self.request.link(SiteLocale(locale, to))

        return [
            (get_name(locale), get_link(locale))
            for locale in sorted(self.app.locales)
        ]

    def format_name(self, item):
        return item.name if item.entity_id else _("Expats")

    @cached_property
    def sentry_js(self):
        return self.app.sentry_js
