from decimal import Decimal
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.layouts import DefaultLayout
from onegov.swissvotes.layouts import DeleteVoteLayout
from onegov.swissvotes.layouts import DeleteVotesLayout
from onegov.swissvotes.layouts import EditPageLayout
from onegov.swissvotes.layouts import MailLayout
from onegov.swissvotes.layouts import PageLayout
from onegov.swissvotes.layouts import UpdateVotesLayout
from onegov.swissvotes.layouts import UploadVoteAttachemtsLayout
from onegov.swissvotes.layouts import VoteLayout
from onegov.swissvotes.layouts import VotesLayout
from onegov.swissvotes.layouts import VoteStrengthsLayout
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import TranslatablePage


class DummyPrincipal(object):
    pass


class DummyApp(object):
    principal = DummyPrincipal()
    theme_options = {}


class DummyRequest(object):
    app = DummyApp()
    is_logged_in = False
    locale = 'de_CH'
    roles = []
    includes = []
    session = None
    url = ''

    def has_role(self, *roles):
        return any((role in self.roles for role in roles))

    def translate(self, text):
        return str(text)

    def include(self, *args, **kwargs):
        self.includes.extend(args)

    def link(self, model, name=''):
        if isinstance(model, str):
            return f'{model}/{name}'
        return f'{model.__class__.__name__}/{name}'

    def exclude_invisible(self, objects):
        return objects

    def new_csrf_token(self):
        return 'x'


def path(links):
    return '/'.join([link.attrs['href'].strip('/') for link in links])


def hrefs(items):
    for item in items:
        if hasattr(item, 'links'):
            for ln in item.links:
                yield (
                    ln.attrs.get('href')
                    or ln.attrs.get('ic-delete-from')
                    or ln.attrs.get('ic-post-to')
                )
        else:
            yield (
                item.attrs.get('href')
                or item.attrs.get('ic-delete-from')
                or item.attrs.get('ic-post-to')
            )


def test_layout_default(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    request.session = swissvotes_app.session()
    model = None

    layout = DefaultLayout(model, request)
    assert layout.title == ""
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal'
    assert layout.static_path == 'Principal/static'
    assert layout.app_version
    assert layout.locales == [
        ('de_CH', 'de', 'Deutsch', 'SiteLocale/'),
        ('fr_CH', 'fr', 'Français', 'SiteLocale/'),
        ('en_US', 'en', 'English', 'SiteLocale/')
    ]
    assert layout.request.includes == ['frameworks', 'chosen', 'common']
    assert layout.top_navigation == [
        ('Votes', 'SwissVoteCollection/'),
        ('Datensatz', 'TranslatablePage/'),
        ('Über uns', 'TranslatablePage/'),
        ('Kontakt', 'TranslatablePage/')
    ]
    assert layout.homepage_url == 'Principal/'
    assert layout.votes_url == 'SwissVoteCollection/'
    assert layout.login_url == 'Auth/login'
    assert layout.logout_url is None
    assert path([layout.disclaimer_link]) == 'TranslatablePage'
    assert path([layout.imprint_link]) == 'TranslatablePage'

    assert layout.format_bfs_number(Decimal('100')) == '100'
    assert layout.format_bfs_number(Decimal('100.1')) == '100.1'
    assert layout.format_bfs_number(Decimal('100.12')) == '100.1'

    assert layout.format_procedure_number(None) == ''
    assert layout.format_procedure_number(Decimal('0')) == '0'
    assert layout.format_procedure_number(Decimal('00.087')) == '00.087'
    assert layout.format_procedure_number(Decimal('0.087')) == '00.087'
    assert layout.format_procedure_number(Decimal('02.060')) == '02.060'
    assert layout.format_procedure_number(Decimal('2.06')) == '02.060'
    assert layout.format_procedure_number(Decimal('16.479')) == '16.479'
    assert layout.format_procedure_number(Decimal('1859')) == '1859'
    assert layout.format_procedure_number(Decimal('1859.000')) == '1859'
    assert layout.format_procedure_number(Decimal('9309')) == '9309'
    assert layout.format_procedure_number(Decimal('9309.0')) == '9309'
    assert layout.format_procedure_number(Decimal('12239')) == '12239'
    assert layout.format_procedure_number(Decimal('12239.0')) == '12239'

    # Login
    request.is_logged_in = True
    layout = DefaultLayout(model, request)
    assert layout.login_url is None
    assert layout.logout_url == 'Auth/logout'

    # Remove initial content
    layout.pages.query().delete()
    assert layout.top_navigation == [('Votes', 'SwissVoteCollection/')]
    assert layout.disclaimer_link is None
    assert layout.imprint_link is None

    assert layout.format_policy_areas(SwissVote()) == ''

    vote = SwissVote(
        descriptor_1_level_1=Decimal('4'),
        descriptor_2_level_1=Decimal('8'),
        descriptor_2_level_2=Decimal('8.3'),
        descriptor_3_level_1=Decimal('10'),
        descriptor_3_level_2=Decimal('10.3'),
        descriptor_3_level_3=Decimal('10.33'),
    )
    assert layout.format_policy_areas(vote) == (
        '<span title="d-1-10 &gt; d-2-103 &gt; d-3-1033">d-1-10</span>,<br>'
        '<span title="d-1-4">d-1-4</span>,<br>'
        '<span title="d-1-8 &gt; d-2-83">d-1-8</span>'
    )

    vote = SwissVote(
        descriptor_2_level_1=Decimal('10'),
        descriptor_2_level_2=Decimal('10.3'),
        descriptor_3_level_1=Decimal('10'),
        descriptor_3_level_2=Decimal('10.3'),
        descriptor_3_level_3=Decimal('10.33'),
    )
    assert layout.format_policy_areas(vote) == (
        '<span title="d-1-10 &gt; d-2-103 &#10;&#10;'
        'd-1-10 &gt; d-2-103 &gt; d-3-1033">d-1-10</span>'
    )


def test_layout_mail():
    request = DummyRequest()
    model = None

    layout = MailLayout(model, request)
    assert layout.primary_color == '#fff'


def test_layout_page(session):
    request = DummyRequest()
    model = TranslatablePage(
        id='page',
        title_translations={'en_US': "Page", 'de_CH': "Seite"},
        content_translations={'en_US': "Content", 'de_CH': "Inhalt"}
    )
    session.add(model)
    session.flush()

    layout = PageLayout(model, request)
    assert layout.title == "Seite"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/#'

    # Log in as editor
    request.roles = ['editor']
    layout = PageLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'TranslatablePage/edit'
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = PageLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'TranslatablePage/edit',
    ]


def test_layout_edit_page(session):
    request = DummyRequest()
    model = TranslatablePage(
        id='page',
        title_translations={'en_US': "Page", 'de_CH': "Seite"},
        content_translations={'en_US': "Content", 'de_CH': "Inhalt"}
    )
    session.add(model)
    session.flush()

    layout = EditPageLayout(model, request)
    assert layout.title == "Edit page"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/TranslatablePage/#'

    # Log in as editor
    request.roles = ['editor']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []


def test_layout_vote():
    request = DummyRequest()
    model = SwissVote(title="Vote")

    layout = VoteLayout(model, request)
    assert layout.title == "Vote"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/SwissVoteCollection/#'

    # Log in as editor
    request.roles = ['editor']
    layout = VoteLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVote/upload',
        'SwissVote/delete',
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = VoteLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVote/upload',
        'SwissVote/delete',
    ]


def test_layout_vote_strengths():
    request = DummyRequest()
    model = SwissVote(title="Vote")

    layout = VoteStrengthsLayout(model, request)
    assert layout.title == _("Voter strengths")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/SwissVoteCollection/SwissVote/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = VoteStrengthsLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = VoteStrengthsLayout(model, request)
    assert layout.editbar_links == []


def test_layout_upload_vote_attachemts():
    request = DummyRequest()
    model = SwissVote(title="Vote")

    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.title == _("Manage attachments")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/SwissVoteCollection/SwissVote/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_vote():
    request = DummyRequest()
    model = SwissVote(title="Vote")

    layout = DeleteVoteLayout(model, request)
    assert layout.title == _("Delete vote")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/SwissVoteCollection/SwissVote/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = DeleteVoteLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeleteVoteLayout(model, request)
    assert layout.editbar_links == []


def test_layout_votes():
    request = DummyRequest()
    model = SwissVoteCollection(None)

    layout = VotesLayout(model, request)
    assert layout.title == _("Votes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/SwissVoteCollection'

    # Log in as editor
    request.roles = ['editor']
    layout = VotesLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVoteCollection/update',
        'SwissVoteCollection/csv',
        'SwissVoteCollection/xlsx'
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = VotesLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVoteCollection/update',
        'SwissVoteCollection/csv',
        'SwissVoteCollection/xlsx',
        'SwissVoteCollection/delete',
    ]


def test_layout_update_votes():
    request = DummyRequest()
    model = SwissVoteCollection(None)

    layout = UpdateVotesLayout(model, request)
    assert layout.title == _("Update dataset")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/SwissVoteCollection/#'

    # Log in as editor
    request.roles = ['editor']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_votes():
    request = DummyRequest()
    model = SwissVoteCollection(None)

    layout = DeleteVotesLayout(model, request)
    assert layout.title == _("Delete all votes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/SwissVoteCollection/#'

    # Log in as editor
    request.roles = ['editor']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []
