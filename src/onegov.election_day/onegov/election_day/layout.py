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
    def subscribe_link(self):
        return self.request.link(self.principal, 'subscribe')

    @cached_property
    def unsubscribe_link(self):
        return self.request.link(self.principal, 'unsubscribe')

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


class DefaultLayout(Layout):
    pass


class ElectionsLayout(Layout):

    @cached_property
    def all_tabs(self):
        return (
            'lists',
            'candidates',
            'districts',
            'connections',
            'parties',
            'statistics',
            'panachage',
            'data'
        )

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'lists':
            return _("Lists")
        if tab == 'candidates':
            return _("Candidates")
        if tab == 'districts':
            return _("Electoral Districts")
        if tab == 'connections':
            return _("List connections")
        if tab == 'parties':
            return _("Parties")
        if tab == 'statistics':
            return _("Election statistics")
        if tab == 'panachage':
            return _("Panachage")
        if tab == 'data':
            return _("Open Data")

        return ''

    def visible(self, tab=None):
        if not self.has_results:
            return False

        tab = self.tab if tab is None else tab

        if tab == 'lists':
            return self.proporz
        if tab == 'parties':
            return self.proporz and self.model.party_results.first()
        if tab == 'districts':
            return self.majorz and self.summarize
        if tab == 'connections':
            return self.proporz and self.model.list_connections.first()
        if tab == 'panachage':
            return self.proporz and self.model.has_panachage_data

        return True

    @cached_property
    def has_results(self):
        if self.model.results.first():
            return True
        return False

    @cached_property
    def majorz(self):
        if self.model.type == 'majorz':
            return True
        return False

    @cached_property
    def proporz(self):
        if self.model.type == 'proporz':
            return True
        return False

    @cached_property
    def counted(self):
        if self.has_results and self.model.counted:
            return True
        return False

    @cached_property
    def summarize(self):
        return self.model.total_entities != 1

    @cached_property
    def main_view(self):
        if self.proporz:
            return self.request.link(self.model, 'lists')
        return self.request.link(self.model, 'candidates')

    @cached_property
    def menu(self):
        return (
            (
                self.title(tab),
                self.request.link(self.model, tab),
                'active' if self.tab == tab else ''
            ) for tab in self.all_tabs if self.visible(tab)
        )

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab


class VotesLayout(Layout):

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'proposal':
            return _("Proposal")
        if tab == 'counter-proposal':
            return _("Counter Proposal")
        if tab == 'tie-breaker':
            return _("Tie-Breaker")
        if tab == 'data':
            return _("Open Data")

        return ''

    @cached_property
    def ballot(self):
        if self.tab == 'counter-proposal':
            return self.model.counter_proposal
        if self.tab == 'tie-breaker':
            return self.model.tie_breaker
        return self.model.proposal

    def visible(self, tab=None):
        if not self.has_results:
            return False

        tab = self.tab if tab is None else tab

        if tab == 'proposal':
            return True
        if self.tab == 'counter-proposal' or self.tab == 'tie-breaker':
            return self.counter_proposal

        return True

    @cached_property
    def has_results(self):
        if self.model.ballots.first():
            return True
        return False

    @cached_property
    def counter_proposal(self):
        return self.model.counter_proposal

    @cached_property
    def counted(self):
        return self.has_results and self.model.counted

    @cached_property
    def summarize(self):
        return self.ballot.results.count() != 1

    @cached_property
    def menu(self):
        if not self.has_results:
            return []

        if not self.counter_proposal:
            return (
                (
                    self.title('proposal'),
                    self.request.link(self.model),
                    'active' if self.tab == 'proposal' else ''
                ), (
                    self.title('data'),
                    self.request.link(self.model, 'data'),
                    'active' if self.tab == 'data' else ''
                )
            )

        return (
            (
                self.title('proposal'),
                self.request.link(self.model),
                'active' if self.tab == 'proposal' else ''
            ), (
                self.title('counter-proposal'),
                self.request.link(self.model, 'counter-proposal'),
                'active' if self.tab == 'counter-proposal' else ''
            ), (
                self.title('tie-breaker'),
                self.request.link(self.model, 'tie-breaker'),
                'active' if self.tab == 'tie-breaker' else ''
            ), (
                self.title('data'),
                self.request.link(self.model, 'data'),
                'active' if self.tab == 'data' else ''
            )
        )

    def __init__(self, model, request, tab='proposal'):
        super().__init__(model, request)
        self.tab = tab


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
