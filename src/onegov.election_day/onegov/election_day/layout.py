from babel import Locale
from cached_property import cached_property
from datetime import datetime
from onegov.ballot import ElectionCollection, VoteCollection
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.election_day import _
from onegov.election_day.collections import ArchivedResultCollection
from onegov.user import Auth


class Layout(ChameleonLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('common')

    @cached_property
    def principal(self):
        return self.request.app.principal

    @cached_property
    def homepage_link(self):
        return self.request.link(self.principal)

    @cached_property
    def opendata_link(self):
        lang = (self.request.locale or 'en')[:2]
        return (
            "https://github.com/OneGov/onegov.election_day"
            "/blob/master/docs/open_data_{}.md"
        ).format(lang)

    @cached_property
    def format_description_link(self):
        lang = (self.request.locale or 'en')[:2]
        return (
            "https://github.com/OneGov/onegov.election_day"
            "/blob/master/docs/format_{}.md"
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
        return ArchivedResultCollection(self.request.app.session())

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

    @cached_property
    def notifications(self):
        return len(self.principal.webhooks) > 0


class DefaultLayout(Layout):
    pass


class ManageLayout(DefaultLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(self.model)

    @cached_property
    def menu(self):
        menu = []
        session = self.request.app.session()

        link = self.request.link(VoteCollection(session))
        class_ = 'active' if link == self.manage_model_link else ''
        menu.append((_("Votes"), link, class_))

        link = self.request.link(ElectionCollection(session))
        class_ = 'active' if link == self.manage_model_link else ''
        menu.append((_("Elections"), link, class_))

        return menu

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('form')
        self.breadcrumbs = [
            (_("Manage"), super().manage_link, 'unavailable'),
        ]


class ManageElectionsLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            ElectionCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Elections"), request.link(self.model), '')
        )


class ManageVotesLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            VoteCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Votes"), request.link(self.model), ''),
        )
