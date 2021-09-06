from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.utils import Bunch
from onegov.file.utils import as_fileintent
from onegov.swissvotes import _
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.layouts import AddPageLayout
from onegov.swissvotes.layouts import DefaultLayout
from onegov.swissvotes.layouts import DeletePageAttachmentLayout
from onegov.swissvotes.layouts import DeletePageLayout
from onegov.swissvotes.layouts import DeleteVoteAttachmentLayout
from onegov.swissvotes.layouts import DeleteVoteLayout
from onegov.swissvotes.layouts import DeleteVotesLayout
from onegov.swissvotes.layouts import EditPageLayout
from onegov.swissvotes.layouts import MailLayout
from onegov.swissvotes.layouts import ManageCampaingMaterialNayLayout
from onegov.swissvotes.layouts import ManageCampaingMaterialYeaLayout
from onegov.swissvotes.layouts import ManagePageAttachmentsLayout
from onegov.swissvotes.layouts import ManagePageSliderImagesLayout
from onegov.swissvotes.layouts import PageLayout
from onegov.swissvotes.layouts import UpdateExternalResourcesLayout
from onegov.swissvotes.layouts import UpdateVotesLayout
from onegov.swissvotes.layouts import UploadVoteAttachemtsLayout
from onegov.swissvotes.layouts import VoteLayout
from onegov.swissvotes.layouts import VotesLayout
from onegov.swissvotes.layouts import VoteStrengthsLayout
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import TranslatablePage
from onegov.swissvotes.models import TranslatablePageFile
from psycopg2.extras import NumericRange
from pytest import mark


class DummyPrincipal(object):
    pass


class DummyApp(object):
    principal = DummyPrincipal()
    theme_options = {}
    static_content_pages = {'home'}


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
        if hasattr(model, 'bfs_number'):
            return f'{model.__class__.__name__}/{model.bfs_number}/{name}'
        if hasattr(model, 'id'):
            return f'{model.__class__.__name__}/{model.id}/{name}'
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
    session = swissvotes_app.session()

    request = DummyRequest()
    request.app = swissvotes_app
    request.session = session
    model = None

    layout = DefaultLayout(model, request)
    assert layout.title == ""
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal'
    assert layout.static_path == 'Principal/static'
    assert layout.locales == [
        ('de_CH', 'de', 'Deutsch', 'SiteLocale/'),
        ('fr_CH', 'fr', 'Français', 'SiteLocale/'),
        ('en_US', 'en', 'English', 'SiteLocale/')
    ]
    assert layout.request.includes == ['frameworks', 'chosen', 'common']
    assert list(hrefs(layout.top_navigation)) == ['SwissVoteCollection/']
    assert layout.homepage_url == 'Principal/'
    assert layout.votes_url == 'SwissVoteCollection/'
    assert layout.login_url == 'Auth/login'
    assert layout.logout_url is None
    assert layout.move_page_url_template == (
        'TranslatablePageMove/?csrf-token=x'
    )
    assert path([layout.disclaimer_link]) == 'TranslatablePage/disclaimer'
    layout.disclaimer_link.text == 'disclaimer'
    assert path([layout.imprint_link]) == 'TranslatablePage/imprint'
    layout.imprint_link.text == 'imprint'
    assert path([layout.data_protection_link]) == (
        'TranslatablePage/data-protection'
    )
    layout.data_protection_link.text == 'data-protection'

    # Login
    request.is_logged_in = True
    layout = DefaultLayout(model, request)
    assert layout.login_url is None
    assert layout.logout_url == 'Auth/logout'

    # Add some pages
    pages = TranslatablePageCollection(session)
    pages.add(
        id='dataset',
        title_translations={'de_CH': 'Datensatz', 'en_US': 'Dataset'},
        content_translations={'de_CH': 'Datensatz', 'en_US': 'Dataset'}
    )
    pages.add(
        id='about',
        title_translations={'de_CH': 'Über uns', 'en_US': 'About'},
        content_translations={'de_CH': 'Über uns', 'en_US': 'About'}
    )
    pages.add(
        id='contact',
        title_translations={'de_CH': 'Kontakt', 'en_US': 'Contact'},
        content_translations={'de_CH': 'Kontakt', 'en_US': 'Contact'}
    )
    assert [item.text for item in layout.top_navigation] == [
        'Votes',
        'Datensatz',
        'Über uns',
        'Kontakt'
    ]

    assert layout.format_number(None) == ''
    assert layout.format_number(1) == '1'
    assert layout.format_number(2) == '2'
    assert layout.format_number(3) == '3'
    assert layout.format_number(1.111, 0) == '1'
    assert layout.format_number(1.111, 1) == '1.1'
    assert layout.format_number(1.111, 2) == '1.11'
    assert layout.format_number(1.111, 3) == '1.111'
    assert layout.format_number(1.111, 4) == '1.1110'
    assert layout.format_number(4.444, 0) == '4'
    assert layout.format_number(4.444, 1) == '4.4'
    assert layout.format_number(4.444, 2) == '4.44'
    assert layout.format_number(4.444, 3) == '4.444'
    assert layout.format_number(4.444, 4) == '4.4440'
    assert layout.format_number(5.555, 0) == '6'
    assert layout.format_number(5.555, 1) == '5.6'
    # assert layout.format_number(5.555, 2) == '5.56'
    assert layout.format_number(5.555, 3) == '5.555'
    assert layout.format_number(5.555, 4) == '5.5550'
    assert layout.format_number(6.555, 0) == '7'
    assert layout.format_number(6.555, 1) == '6.6'
    # assert layout.format_number(6.555, 2) == '6.56'
    assert layout.format_number(6.555, 3) == '6.555'
    assert layout.format_number(6.555, 4) == '6.5550'
    assert layout.format_number(8.888, 0) == '9'
    assert layout.format_number(8.888, 1) == '8.9'
    assert layout.format_number(8.888, 2) == '8.89'
    assert layout.format_number(8.888, 3) == '8.888'
    assert layout.format_number(8.888, 4) == '8.8880'
    assert layout.format_number(9.999, 0) == '10'
    assert layout.format_number(9.999, 1) == '10.0'
    assert layout.format_number(9.999, 2) == '10.00'
    assert layout.format_number(9.999, 3) == '9.999'
    assert layout.format_number(9.999, 4) == '9.9990'
    assert layout.format_number(Decimal('1.111'), 0) == '1'
    assert layout.format_number(Decimal('1.111'), 1) == '1.1'
    assert layout.format_number(Decimal('1.111'), 2) == '1.11'
    assert layout.format_number(Decimal('1.111'), 3) == '1.111'
    assert layout.format_number(Decimal('1.111'), 4) == '1.1110'
    assert layout.format_number(Decimal('4.444'), 0) == '4'
    assert layout.format_number(Decimal('4.444'), 1) == '4.4'
    assert layout.format_number(Decimal('4.444'), 2) == '4.44'
    assert layout.format_number(Decimal('4.444'), 3) == '4.444'
    assert layout.format_number(Decimal('4.444'), 4) == '4.4440'
    assert layout.format_number(Decimal('5.555'), 0) == '6'
    assert layout.format_number(Decimal('5.555'), 1) == '5.6'
    assert layout.format_number(Decimal('5.555'), 2) == '5.56'
    assert layout.format_number(Decimal('5.555'), 3) == '5.555'
    assert layout.format_number(Decimal('5.555'), 4) == '5.5550'
    assert layout.format_number(Decimal('6.555'), 0) == '7'
    assert layout.format_number(Decimal('6.555'), 1) == '6.6'
    assert layout.format_number(Decimal('6.555'), 2) == '6.56'
    assert layout.format_number(Decimal('6.555'), 3) == '6.555'
    assert layout.format_number(Decimal('6.555'), 4) == '6.5550'
    assert layout.format_number(Decimal('8.888'), 0) == '9'
    assert layout.format_number(Decimal('8.888'), 1) == '8.9'
    assert layout.format_number(Decimal('8.888'), 2) == '8.89'
    assert layout.format_number(Decimal('8.888'), 3) == '8.888'
    assert layout.format_number(Decimal('8.888'), 4) == '8.8880'
    assert layout.format_number(Decimal('9.999'), 0) == '10'
    assert layout.format_number(Decimal('9.999'), 1) == '10.0'
    assert layout.format_number(Decimal('9.999'), 2) == '10.00'
    assert layout.format_number(Decimal('9.999'), 3) == '9.999'
    assert layout.format_number(Decimal('9.999'), 4) == '9.9990'
    assert layout.format_number(-1.111, 0) == '-1'
    assert layout.format_number(-1.111, 1) == '-1.1'
    assert layout.format_number(-1.111, 2) == '-1.11'
    assert layout.format_number(-1.111, 3) == '-1.111'
    assert layout.format_number(-1.111, 4) == '-1.1110'
    assert layout.format_number(-4.444, 0) == '-4'
    assert layout.format_number(-4.444, 1) == '-4.4'
    assert layout.format_number(-4.444, 2) == '-4.44'
    assert layout.format_number(-4.444, 3) == '-4.444'
    assert layout.format_number(-4.444, 4) == '-4.4440'
    assert layout.format_number(-5.555, 0) == '-6'
    assert layout.format_number(-5.555, 1) == '-5.6'
    # assert layout.format_number(-5.555, 2) == '-5.56'
    assert layout.format_number(-5.555, 3) == '-5.555'
    assert layout.format_number(-5.555, 4) == '-5.5550'
    assert layout.format_number(-6.555, 0) == '-7'
    assert layout.format_number(-6.555, 1) == '-6.6'
    # assert layout.format_number(-6.555, 2) == '-6.56'
    assert layout.format_number(-6.555, 3) == '-6.555'
    assert layout.format_number(-6.555, 4) == '-6.5550'
    assert layout.format_number(-8.888, 0) == '-9'
    assert layout.format_number(-8.888, 1) == '-8.9'
    assert layout.format_number(-8.888, 2) == '-8.89'
    assert layout.format_number(-8.888, 3) == '-8.888'
    assert layout.format_number(-8.888, 4) == '-8.8880'
    assert layout.format_number(-9.999, 0) == '-10'
    assert layout.format_number(-9.999, 1) == '-10.0'
    assert layout.format_number(-9.999, 2) == '-10.00'
    assert layout.format_number(-9.999, 3) == '-9.999'
    assert layout.format_number(-9.999, 4) == '-9.9990'
    assert layout.format_number(Decimal('-1.111'), 0) == '-1'
    assert layout.format_number(Decimal('-1.111'), 1) == '-1.1'
    assert layout.format_number(Decimal('-1.111'), 2) == '-1.11'
    assert layout.format_number(Decimal('-1.111'), 3) == '-1.111'
    assert layout.format_number(Decimal('-1.111'), 4) == '-1.1110'
    assert layout.format_number(Decimal('-4.444'), 0) == '-4'
    assert layout.format_number(Decimal('-4.444'), 1) == '-4.4'
    assert layout.format_number(Decimal('-4.444'), 2) == '-4.44'
    assert layout.format_number(Decimal('-4.444'), 3) == '-4.444'
    assert layout.format_number(Decimal('-4.444'), 4) == '-4.4440'
    assert layout.format_number(Decimal('-5.555'), 0) == '-6'
    assert layout.format_number(Decimal('-5.555'), 1) == '-5.6'
    assert layout.format_number(Decimal('-5.555'), 2) == '-5.56'
    assert layout.format_number(Decimal('-5.555'), 3) == '-5.555'
    assert layout.format_number(Decimal('-5.555'), 4) == '-5.5550'
    assert layout.format_number(Decimal('-6.555'), 0) == '-7'
    assert layout.format_number(Decimal('-6.555'), 1) == '-6.6'
    assert layout.format_number(Decimal('-6.555'), 2) == '-6.56'
    assert layout.format_number(Decimal('-6.555'), 3) == '-6.555'
    assert layout.format_number(Decimal('-6.555'), 4) == '-6.5550'
    assert layout.format_number(Decimal('-8.888'), 0) == '-9'
    assert layout.format_number(Decimal('-8.888'), 1) == '-8.9'
    assert layout.format_number(Decimal('-8.888'), 2) == '-8.89'
    assert layout.format_number(Decimal('-8.888'), 3) == '-8.888'
    assert layout.format_number(Decimal('-8.888'), 4) == '-8.8880'
    assert layout.format_number(Decimal('-9.999'), 0) == '-10'
    assert layout.format_number(Decimal('-9.999'), 1) == '-10.0'
    assert layout.format_number(Decimal('-9.999'), 2) == '-10.00'
    assert layout.format_number(Decimal('-9.999'), 3) == '-9.999'
    assert layout.format_number(Decimal('-9.999'), 4) == '-9.9990'

    assert layout.format_bfs_number(Decimal('100')) == '100'
    assert layout.format_bfs_number(Decimal('100.1')) == '100.1'
    assert layout.format_bfs_number(Decimal('100.12')) == '100.1'

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
        '<span title="d-1-4">d-1-4</span>,<br>'
        '<span title="d-1-8 &gt; d-2-83">d-1-8</span>,<br>'
        '<span title="d-1-10 &gt; d-2-103 &gt; d-3-1033">d-1-10</span>'
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
        'TranslatablePage/page/edit',
        'TranslatablePage/page/attachments',
        'TranslatablePage/page/slider-images',
        'TranslatablePage/page/delete',
        'TranslatablePageCollection/add'
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = PageLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'TranslatablePage/page/edit',
        'TranslatablePage/page/attachments',
        'TranslatablePage/page/slider-images',
        'TranslatablePage/page/delete',
        'TranslatablePageCollection/add'
    ]

    # Static page
    model.id = 'home'
    layout = PageLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'TranslatablePage/home/edit',
        'TranslatablePage/home/attachments',
        'TranslatablePage/home/slider-images',
        'TranslatablePageCollection/add'
    ]


def test_layout_page_slides(swissvotes_app, slider_images):
    session = swissvotes_app.session()
    votes = {
        bfs_number: SwissVote(
            title_de=f'Vote {bfs_number} DE',
            title_fr=f'Vote {bfs_number} FR',
            short_title_de='Vote D',
            short_title_fr='Vote F',
            bfs_number=Decimal(bfs_number),
            date=date(1990, 6, 2),
            legislation_number=10,
            legislation_decade=NumericRange(1990, 1994),
            votes_on_same_day=2,
            _legal_form=1
        ) for bfs_number in ('1', '2.1', '2.2')
    }
    for vote in votes.values():
        session.add(vote)
    session.flush()

    request = DummyRequest()
    request.app = swissvotes_app
    model = TranslatablePage(
        id='page',
        title_translations={'en_US': "Page", 'de_CH': "Seite"},
        content_translations={'en_US': "Content", 'de_CH': "Inhalt"}
    )
    session.add(model)
    session.flush()

    for file in slider_images.values():
        model.files.append(file)
    assert len(model.slider_images) == 6

    layout = PageLayout(model, request)
    assert layout.slides == [
        Bunch(
            image='TranslatablePageFile/{}/'.format(slider_images['1-1'].id),
            url='SwissVote/{}/'.format(votes['1'].bfs_number),
            label=votes['1'].title,
        ),
        Bunch(
            image='TranslatablePageFile/{}/'.format(slider_images['1'].id),
            url='SwissVote/{}/'.format(votes['1'].bfs_number),
            label=votes['1'].title,
        ),
        Bunch(
            image='TranslatablePageFile/{}/'.format(slider_images['2.1-x'].id),
            url='SwissVote/{}/'.format(votes['2.1'].bfs_number),
            label=votes['2.1'].title,
        ),
        Bunch(
            image='TranslatablePageFile/{}/'.format(slider_images['2.2-x'].id),
            url='SwissVote/{}/'.format(votes['2.2'].bfs_number),
            label=votes['2.2'].title,
        ),
        Bunch(
            image='TranslatablePageFile/{}/'.format(slider_images['2.3-x'].id),
            url='',
            label='2.3-x.png',
        ),
        Bunch(
            image='TranslatablePageFile/{}/'.format(slider_images['n'].id),
            url='',
            label='n.png',
        ),
    ]


def test_layout_add_page(session):
    request = DummyRequest()
    model = TranslatablePageCollection(session)

    layout = AddPageLayout(model, request)
    assert layout.title == "Add page"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/#'

    # Log in as editor
    request.roles = ['editor']
    layout = AddPageLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = AddPageLayout(model, request)
    assert layout.editbar_links == []


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
    assert path(layout.breadcrumbs) == 'DummyPrincipal/TranslatablePage/page/#'

    # Log in as editor
    request.roles = ['editor']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_page(session):
    request = DummyRequest()
    model = TranslatablePage(
        id='page',
        title_translations={'en_US': "Page", 'de_CH': "Seite"},
        content_translations={'en_US': "Content", 'de_CH': "Inhalt"}
    )
    session.add(model)
    session.flush()

    layout = DeletePageLayout(model, request)
    assert layout.title == "Delete page"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/TranslatablePage/page/#'

    # Log in as editor
    request.roles = ['editor']
    layout = DeletePageLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeletePageLayout(model, request)
    assert layout.editbar_links == []


def test_layout_manage_page_attachments(session):
    request = DummyRequest()
    model = TranslatablePage(
        id='page',
        title_translations={'en_US': "Page", 'de_CH': "Seite"},
        content_translations={'en_US': "Content", 'de_CH': "Inhalt"}
    )
    session.add(model)
    session.flush()

    layout = ManagePageAttachmentsLayout(model, request)
    assert layout.title == "Manage attachments"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/TranslatablePage/page/#'

    # Log in as editor
    request.roles = ['editor']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []


def test_layout_mange_page_slides(session):
    request = DummyRequest()
    model = TranslatablePage(
        id='page',
        title_translations={'en_US': "Page", 'de_CH': "Seite"},
        content_translations={'en_US': "Content", 'de_CH': "Inhalt"}
    )
    session.add(model)
    session.flush()

    layout = ManagePageSliderImagesLayout(model, request)
    assert layout.title == "Manage slider images"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/TranslatablePage/page/#'

    # Log in as editor
    request.roles = ['editor']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = EditPageLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_page_attachment(swissvotes_app):
    request = DummyRequest()

    model = TranslatablePageFile(id=random_token())
    model.name = 'attachment-name'
    model.reference = as_fileintent(BytesIO(b'test'), 'filename')

    page = TranslatablePage(
        id='page',
        title_translations={'en_US': "Page", 'de_CH': "Seite"},
        content_translations={'en_US': "Content", 'de_CH': "Inhalt"}
    )
    session = swissvotes_app.session()
    session.add(page)
    session.flush()
    page.files.append(model)

    layout = DeletePageAttachmentLayout(model, request)
    assert layout.title == "Delete attachment"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/TranslatablePage/page/#'

    # Log in as editor
    request.roles = ['editor']
    layout = DeletePageAttachmentLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeletePageAttachmentLayout(model, request)
    assert layout.editbar_links == []


def test_layout_vote(swissvotes_app):
    session = swissvotes_app.session()
    request = DummyRequest()
    request.app = swissvotes_app
    session.add(SwissVote(
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="Vote D",
        short_title_fr="Vote F",
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        legislation_number=10,
        legislation_decade=NumericRange(1990, 1994),
        votes_on_same_day=2,
        _legal_form=1
    ))
    session.flush()
    model = session.query(SwissVote).one()

    layout = VoteLayout(model, request)
    assert layout.title == "Vote D"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    swissvotes_app.session_manager.current_locale = 'fr_CH'
    model = swissvotes_app.session().query(SwissVote).one()
    layout = VoteLayout(model, request)
    assert layout.title == "Vote F"

    swissvotes_app.session_manager.current_locale = 'en_US'
    model = swissvotes_app.session().query(SwissVote).one()
    layout = VoteLayout(model, request)
    assert layout.title == "Vote D"

    # Log in as editor
    request.roles = ['editor']
    layout = VoteLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVote/100.00/upload',
        'SwissVote/100.00/manage-campaign-material-yea',
        'SwissVote/100.00/manage-campaign-material-nay',
        'SwissVote/100.00/delete'
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = VoteLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVote/100.00/upload',
        'SwissVote/100.00/manage-campaign-material-yea',
        'SwissVote/100.00/manage-campaign-material-nay',
        'SwissVote/100.00/delete'
    ]


@mark.parametrize('locale', ('de_CH', 'fr_CH', 'en_US'))
def test_layout_vote_file_urls(swissvotes_app, attachments, attachment_urls,
                               locale):
    session = swissvotes_app.session()
    request = DummyRequest()
    request.app = swissvotes_app
    request.locale = locale
    model = SwissVote(
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="Vote D",
        short_title_fr="Vote F",
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        legislation_number=10,
        legislation_decade=NumericRange(1990, 1994),
        votes_on_same_day=2,
        _legal_form=1
    )
    model.session_manager.current_locale = locale
    for name, attachment in attachments.items():
        setattr(model, name, attachment)
    session.add(model)
    session.flush()

    layout = VoteLayout(model, request)
    for attachment in attachments:
        filename = (
            attachment_urls.get(locale, {}).get(attachment)
            or attachment_urls['de_CH'][attachment]  # fallback
        )
        assert layout.attachments[attachment] == f'SwissVote/100/{filename}'


def test_layout_vote_file_urls_fallback(swissvotes_app, attachments,
                                        attachment_urls):
    model = SwissVote(
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="Vote D",
        short_title_fr="Vote F",
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        legislation_number=10,
        legislation_decade=NumericRange(1990, 1994),
        votes_on_same_day=2,
        _legal_form=1
    )
    model.session_manager.current_locale = 'de_CH'
    setattr(model, 'post_vote_poll', attachments['post_vote_poll'])

    session = swissvotes_app.session()
    session.add(model)
    session.flush()

    request = DummyRequest()
    request.app = swissvotes_app
    request.locale = 'fr_CH'

    layout = VoteLayout(model, request)
    assert layout.attachments['post_vote_poll'] == (
        'SwissVote/100/nachbefragung-de.pdf'
    )


def test_layout_vote_strengths(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )

    layout = VoteStrengthsLayout(model, request)
    assert layout.title == _("Voter strengths")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = VoteStrengthsLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = VoteStrengthsLayout(model, request)
    assert layout.editbar_links == []


def test_layout_upload_vote_attachemts(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )

    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.title == _("Manage attachments")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_vote(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )

    layout = DeleteVoteLayout(model, request)
    assert layout.title == _("Delete vote")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = DeleteVoteLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeleteVoteLayout(model, request)
    assert layout.editbar_links == []


def test_layout_votes(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVoteCollection(swissvotes_app)

    layout = VotesLayout(model, request)
    assert layout.title == _("Votes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection'

    # Log in as editor
    request.roles = ['editor']
    layout = VotesLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVoteCollection/update',
        'SwissVoteCollection/update-external-resources',
        'SwissVoteCollection/csv',
        'SwissVoteCollection/xlsx',
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = VotesLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVoteCollection/update',
        'SwissVoteCollection/update-external-resources',
        'SwissVoteCollection/csv',
        'SwissVoteCollection/xlsx',
        'SwissVoteCollection/delete',
    ]


def test_layout_update_votes(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVoteCollection(swissvotes_app)

    layout = UpdateVotesLayout(model, request)
    assert layout.title == _("Update dataset")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    # Log in as editor
    request.roles = ['editor']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []


def test_layout_update_external_resources(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVoteCollection(swissvotes_app)

    layout = UpdateExternalResourcesLayout(model, request)
    assert layout.title == _('Update external resources')
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    # Log in as editor
    request.roles = ['editor']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []


def test_layout_manage_campaign_material_yea(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )

    layout = ManageCampaingMaterialYeaLayout(model, request)
    assert layout.title == _("Campaign material for a Yes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []


def test_layout_manage_campaign_material_nay(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )

    layout = ManageCampaingMaterialNayLayout(model, request)
    assert layout.title == _("Campaign material for a No")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_votes(swissvotes_app):
    request = DummyRequest()
    request.app = swissvotes_app
    model = SwissVoteCollection(swissvotes_app)

    layout = DeleteVotesLayout(model, request)
    assert layout.title == _("Delete all votes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    # Log in as editor
    request.roles = ['editor']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_vote_attachment(swissvotes_app, attachments):
    request = DummyRequest()
    request.app = swissvotes_app
    vote = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )
    vote.ad_analysis = attachments['ad_analysis']
    model = vote.ad_analysis

    layout = DeleteVoteAttachmentLayout(model, request)
    assert layout.title == _("Delete attachment")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []
