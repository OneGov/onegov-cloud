from babel import Locale
from cached_property import cached_property
from datetime import datetime
from onegov.ballot import ElectionCollection
from onegov.ballot import VoteCollection
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import SubscriberCollection
from onegov.election_day.utils import pdf_filename, svg_filename
from onegov.user import Auth


class Layout(ChameleonLayout):

    day_long_format = 'dd. MMMM'

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('common')
        self.request.include('custom')

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
    def format_description_link(self):
        lang = (self.request.locale or 'en')[:2]
        return (
            "https://github.com/OneGov/onegov.election_day"
            "/blob/master/docs/format__{}.md"
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

    def format_group(self, item):
        return item.group if item.entity_id else _("Expats")

    @cached_property
    def sentry_js(self):
        return self.app.sentry_js


class DefaultLayout(Layout):
    pass


class ElectionsLayout(Layout):

    def __init__(self, model, request, tab=None):
        super().__init__(model, request)
        self.tab = tab

    @cached_property
    def all_tabs(self):
        return (
            'lists',
            'candidates',
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
        if tab == 'connections':
            return _("List connections")
        if tab == 'parties':
            return _("Parties")
        if tab == 'statistics':
            return _("Election statistics")
        if tab == 'panachage':
            return _("Panachage")
        if tab == 'data':
            return _("Downloads")

        return ''

    def visible(self, tab=None):
        if not self.has_results:
            return False

        tab = self.tab if tab is None else tab

        if tab == 'lists':
            return self.proporz
        if tab == 'parties':
            return self.proporz and self.model.party_results.first()
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
    def summarize(self):
        return self.model.total_entities != 1

    @cached_property
    def main_view(self):
        if self.proporz:
            return self.request.link(self.model, 'lists')
        return self.request.link(self.model, 'candidates')

    @cached_property
    def menu(self):
        return [
            (
                self.title(tab),
                self.request.link(self.model, tab),
                'active' if self.tab == tab else ''
            ) for tab in self.all_tabs if self.visible(tab)
        ]

    @cached_property
    def pdf_path(self):
        """ Returns the path to the PDF file or None, if it is not available.
        """

        path = 'pdf/{}'.format(pdf_filename(self.model, self.request.locale))
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_path(self):
        """ Returns the path to the SVG or None, if it is not available. """

        path = 'svg/{}'.format(
            svg_filename(self.model, self.tab)
        )
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_link(self):
        """ Returns a link to the SVG download view. """

        return self.request.link(self.model, name='{}-svg'.format(self.tab))

    @cached_property
    def svg_name(self):
        """ Returns a nice to read SVG filename. """

        return '{}.svg'.format(
            normalize_for_url(
                '{}-{}'.format(
                    self.model.id, self.title() or ''
                )
            )
        )


class VotesLayout(Layout):

    def __init__(self, model, request, tab='proposal'):
        super().__init__(model, request)
        self.tab = tab

    def title(self, tab=None):
        tab = self.tab if tab is None else tab

        if tab == 'proposal':
            return _("Proposal")
        if tab == 'counter-proposal':
            return _("Counter Proposal")
        if tab == 'tie-breaker':
            return _("Tie-Breaker")
        if tab == 'data':
            return _("Downloads")

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
        proposal = self.model.ballots.first()
        if not proposal:
            return False
        return any((r.counted for r in proposal.results))

    @cached_property
    def counter_proposal(self):
        return self.model.counter_proposal

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

    @cached_property
    def pdf_path(self):
        """ Returns the path to the PDF file or None, if it is not available.
        """

        path = 'pdf/{}'.format(pdf_filename(self.model, self.request.locale))
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_path(self):
        """ Returns the path to the SVG file or None, if it is not available.
        """

        path = 'svg/{}'.format(
            svg_filename(self.ballot, 'map', self.request.locale)
        )
        if self.request.app.filestorage.exists(path):
            return path

        return None

    @cached_property
    def svg_link(self):
        """ Returns a link to the SVG download view. """

        return self.request.link(self.ballot, name='svg')

    @cached_property
    def svg_name(self):
        """ Returns a nice to read SVG filename. """

        return '{}.svg'.format(
            normalize_for_url(
                '{}-{}'.format(
                    self.model.id, self.title() or ''
                )
            )
        )


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

        if self.principal.wabsti_import:
            link = self.request.link(DataSourceCollection(session))
            active = (
                link == self.manage_model_link or
                isinstance(self.model, DataSourceItemCollection)
            )
            class_ = 'active' if active else ''
            menu.append((_("Data sources"), link, class_))

        if self.principal.sms_notification:
            link = self.request.link(SubscriberCollection(session))
            class_ = 'active' if link == self.manage_model_link else ''
            menu.append((_("Subscribers"), link, class_))

        return menu

    def title(self):
        try:
            return self.breadcrumbs[-1][0]
        except (IndexError, TypeError):
            return ''

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('backend_common')
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


class ManageSubscribersLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            SubscriberCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Subscribers"), request.link(self.model), ''),
        )


class ManageDataSourcesLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            DataSourceCollection(self.request.app.session())
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (_("Data sources"), request.link(self.model), ''),
        )


class ManageDataSourceItemsLayout(ManageLayout):

    @cached_property
    def manage_model_link(self):
        return self.request.link(
            DataSourceItemCollection(
                self.request.app.session(),
                self.model.id
            )
        )

    def __init__(self, model, request):
        super().__init__(model, request)
        self.breadcrumbs.append(
            (
                _("Data sources"),
                self.request.link(
                    DataSourceCollection(self.request.app.session())
                ),
                ''
            ),
        )
        self.breadcrumbs.append(
            (_("Mappings"), request.link(self.model), ''),
        )
