from __future__ import annotations

import pytest

from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.utils import append_query_param
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
from onegov.swissvotes.layouts import UpdateMetadataLayout
from onegov.swissvotes.layouts import UpdateVotesLayout
from onegov.swissvotes.layouts import UploadVoteAttachemtsLayout
from onegov.swissvotes.layouts import VoteCampaignMaterialLayout
from onegov.swissvotes.layouts import VoteLayout
from onegov.swissvotes.layouts import VotesLayout
from onegov.swissvotes.layouts import VoteStrengthsLayout
from onegov.swissvotes.layouts.page import Slide
from onegov.swissvotes.models import SwissVote
from onegov.swissvotes.models import TranslatablePage
from onegov.swissvotes.models import TranslatablePageFile
from tests.shared.utils import use_locale
from unittest.mock import patch


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from onegov.core.elements import Link, LinkGroup
    from onegov.swissvotes.models import SwissVoteFile
    from sqlalchemy.orm import Session
    from .conftest import TestApp


class DummyPrincipal:
    pass


class DummyApp:
    principal = DummyPrincipal()
    theme_options: dict[str, Any] = {}
    static_content_pages = {'home'}
    version = '1.0'
    sentry_dsn = None


class DummyRequest:
    app: Any = DummyApp()
    is_logged_in = False
    locale = 'de_CH'
    roles: list[str] = []
    includes: list[Any] = []
    session: Any = None
    url = ''
    csrf_token = 'x'

    def has_role(self, *roles: str) -> bool:
        return any(role in self.roles for role in roles)

    def translate(self, text: str) -> str:
        return str(text)

    def include(self, *args: Any, **kwargs: Any) -> None:
        self.includes.extend(args)

    def link(self, obj: object, name: str = '') -> str:
        if isinstance(obj, str):
            return f'{obj}/{name}'
        if hasattr(obj, 'bfs_number'):
            return f'{obj.__class__.__name__}/{obj.bfs_number}/{name}'
        if hasattr(obj, 'id'):
            return f'{obj.__class__.__name__}/{obj.id}/{name}'
        return f'{obj.__class__.__name__}/{name}'

    def class_link(
        self,
        model: type[object],
        variables: dict[str, Any] | None = None,
        name: str = ''
    ) -> str:
        return f'{model.__name__}{variables or ""}/{name}'

    def exclude_invisible(self, objects: Any) -> Any:
        return objects

    def new_csrf_token(self) -> str:
        return self.csrf_token

    def csrf_protected_url(self, url: str) -> str:
        return append_query_param(url, 'csrf-token', self.csrf_token)

    def return_to(self, url: str, redirect: str) -> str:
        return f'{url}{redirect}'


def path(links: Iterable[Link]) -> str:
    return '/'.join(link.attrs['href'].strip('/') for link in links)


def hrefs(items: Iterable[Link | LinkGroup]) -> Iterator[str | None]:
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
                item.attrs.get('href')  # type: ignore[union-attr]
                or item.attrs.get('ic-delete-from')  # type: ignore[union-attr]
                or item.attrs.get('ic-post-to')  # type: ignore[union-attr]
            )


def test_layout_default(swissvotes_app: TestApp) -> None:
    session = swissvotes_app.session()

    request: Any = DummyRequest()
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
    assert request.includes == ['frameworks', 'chosen', 'common']
    assert list(hrefs(layout.top_navigation)) == ['SwissVoteCollection/']
    assert layout.homepage_url == 'Principal/'
    assert layout.votes_url == 'SwissVoteCollection/'
    assert layout.login_url == 'Auth/login'
    assert layout.logout_url is None
    assert layout.move_page_url_template == (
        'TranslatablePageMove{'
        "'subject_id': '{subject_id}', "
        "'target_id': '{target_id}', "
        "'direction': '{direction}'"
        '}/?csrf-token=x'
    )
    assert path([layout.disclaimer_link]) == 'TranslatablePage/disclaimer'
    assert layout.disclaimer_link.text == 'disclaimer'
    assert path([layout.imprint_link]) == 'TranslatablePage/imprint'
    assert layout.imprint_link.text == 'imprint'
    assert path([layout.data_protection_link]) == (
        'TranslatablePage/data-protection'
    )
    assert layout.data_protection_link.text == 'data-protection'

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


def test_layout_format_policy_areas() -> None:
    layout = DefaultLayout(None, DummyRequest())  # type: ignore[arg-type]

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

    vote = SwissVote(
        descriptor_1_level_1=Decimal('10'),
        descriptor_1_level_2=Decimal('10.3'),
        descriptor_2_level_1=Decimal('8'),
        descriptor_3_level_1=Decimal('10'),
        descriptor_3_level_2=Decimal('10.3'),
        descriptor_3_level_3=Decimal('10.33'),
    )
    assert layout.format_policy_areas(vote) == (
        '<span title="d-1-10 &gt; d-2-103 &#10;&#10;d-1-10 &gt;'
        ' d-2-103 &gt; d-3-1033">d-1-10</span>,<br>'
        '<span title="d-1-8">d-1-8</span>'
    )


def test_layout_mail() -> None:
    request: Any = DummyRequest()
    model = None

    layout = MailLayout(model, request)
    assert layout.primary_color == '#fff'


def test_layout_page(session: Session) -> None:
    request: Any = DummyRequest()
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


def test_layout_page_slides(
    swissvotes_app: TestApp,
    slider_images: dict[str, TranslatablePageFile]
) -> None:

    session = swissvotes_app.session()
    votes = {
        bfs_number: SwissVote(
            title_de=f'Vote {bfs_number} DE',
            title_fr=f'Vote {bfs_number} FR',
            short_title_de='Vote D',
            short_title_fr='Vote F',
            bfs_number=Decimal(bfs_number),
            date=date(1990, 6, 2),
            _legal_form=1
        ) for bfs_number in ('1', '2.1', '2.2')
    }
    for vote in votes.values():
        session.add(vote)
    session.flush()

    request: Any = DummyRequest()
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
        Slide(
            image='TranslatablePageFile/{}/'.format(slider_images['1-1'].id),
            url='SwissVote/{}/'.format(votes['1'].bfs_number),
            label=votes['1'].title,
        ),
        Slide(
            image='TranslatablePageFile/{}/'.format(slider_images['1'].id),
            url='SwissVote/{}/'.format(votes['1'].bfs_number),
            label=votes['1'].title,
        ),
        Slide(
            image='TranslatablePageFile/{}/'.format(slider_images['2.1-x'].id),
            url='SwissVote/{}/'.format(votes['2.1'].bfs_number),
            label=votes['2.1'].title,
        ),
        Slide(
            image='TranslatablePageFile/{}/'.format(slider_images['2.2-x'].id),
            url='SwissVote/{}/'.format(votes['2.2'].bfs_number),
            label=votes['2.2'].title,
        ),
        Slide(
            image='TranslatablePageFile/{}/'.format(slider_images['2.3-x'].id),
            url='',
            label='2.3-x.png',
        ),
        Slide(
            image='TranslatablePageFile/{}/'.format(slider_images['n'].id),
            url='',
            label='n.png',
        ),
    ]


def test_layout_add_page(session: Session) -> None:
    request: Any = DummyRequest()
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


def test_layout_edit_page(session: Session) -> None:
    request: Any = DummyRequest()
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


def test_layout_delete_page(session: Session) -> None:
    request: Any = DummyRequest()
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


def test_layout_manage_page_attachments(session: Session) -> None:
    request: Any = DummyRequest()
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
    layout2 = EditPageLayout(model, request)
    assert layout2.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout2 = EditPageLayout(model, request)
    assert layout2.editbar_links == []


def test_layout_mange_page_slides(session: Session) -> None:
    request: Any = DummyRequest()
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
    layout2 = EditPageLayout(model, request)
    assert layout2.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout2 = EditPageLayout(model, request)
    assert layout2.editbar_links == []


def test_layout_delete_page_attachment(swissvotes_app: TestApp) -> None:
    request: Any = DummyRequest()

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


def test_layout_vote(swissvotes_app: TestApp) -> None:
    session = swissvotes_app.session()
    request: Any = DummyRequest()
    request.app = swissvotes_app
    session.add(SwissVote(
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="Vote D",
        short_title_fr="Vote F",
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        _legal_form=1
    ))
    session.flush()
    model = session.query(SwissVote).one()

    layout = VoteLayout(model, request)
    assert layout.title == "Vote D"
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    with use_locale(swissvotes_app, 'fr_CH'):
        model = swissvotes_app.session().query(SwissVote).one()
        layout = VoteLayout(model, request)
        assert layout.title == "Vote F"

    with use_locale(swissvotes_app, 'en_US'):
        model = swissvotes_app.session().query(SwissVote).one()
        layout = VoteLayout(model, request)
        assert layout.title == "Vote D"

    # Log in as editor
    request.roles = ['editor']
    layout = VoteLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVote/100.00/upload',
        'SwissVote/100.00/manage-campaign-material',
        'SwissVote/100.00/manage-campaign-material-yea',
        'SwissVote/100.00/manage-campaign-material-nay',
        'SwissVote/100.00/delete'
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = VoteLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVote/100.00/upload',
        'SwissVote/100.00/manage-campaign-material',
        'SwissVote/100.00/manage-campaign-material-yea',
        'SwissVote/100.00/manage-campaign-material-nay',
        'SwissVote/100.00/delete'
    ]


@pytest.mark.parametrize('locale', ('de_CH', 'fr_CH', 'en_US'))
def test_layout_vote_file_urls(
    swissvotes_app: TestApp,
    attachments: dict[str, SwissVoteFile],
    attachment_urls: dict[str, dict[str, str]],
    locale: str
) -> None:

    session = swissvotes_app.session()
    request: Any = DummyRequest()
    request.app = swissvotes_app
    request.locale = locale
    model = SwissVote(
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="Vote D",
        short_title_fr="Vote F",
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        _legal_form=1
    )
    with use_locale(model, locale):
        for name, attachment in attachments.items():
            setattr(model, name, attachment)
        session.add(model)
        session.flush()

        layout = VoteLayout(model, request)
        for name in attachments:
            filename = (
                attachment_urls.get(locale, {}).get(name)
                or attachment_urls['de_CH'][name]  # fallback
            )
            assert layout.attachments[name] == {
                'locale': locale,
                'url': f'SwissVote/100/{filename}'
            }


def test_layout_vote_file_urls_fallback(
    swissvotes_app: TestApp,
    attachments: dict[str, SwissVoteFile],
    attachment_urls: dict[str, dict[str, str]]
) -> None:

    model = SwissVote(
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="Vote D",
        short_title_fr="Vote F",
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        _legal_form=1
    )
    model.post_vote_poll = attachments['post_vote_poll']

    session = swissvotes_app.session()
    session.add(model)
    session.flush()

    request: Any = DummyRequest()
    request.app = swissvotes_app
    request.locale = 'fr_CH'

    layout = VoteLayout(model, request)
    assert layout.attachments['post_vote_poll'] == {
        'locale': 'de_CH',
        'url': 'SwissVote/100/nachbefragung-de.pdf'
    }


def test_layout_vote_search_results(
    swissvotes_app: TestApp,
    attachments: dict[str, SwissVoteFile],
    campaign_material: dict[str, SwissVoteFile]
) -> None:

    model = SwissVote(
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="Vote D",
        short_title_fr="Vote F",
        bfs_number=Decimal('100'),
        date=date(1990, 6, 2),
        _legal_form=1,
        campaign_material_metadata={
            'campaign_material_other-essay': {
                'title': 'Perché è una pessima idea.',
                'language': ['it', 'rm'],
                'doctype': ['argument']
            },
            'campaign_material_other-article': {
                'title': 'Presseschau',
                'language': ['de'],
                'doctype': 'article'
            },
        }
    )
    for name, locale in (
        ('post_vote_poll', 'de_CH'),
        ('brief_description', 'fr_CH')
    ):
        with use_locale(model, locale):
            setattr(model, name, attachments[name])

    for name in (
        'campaign_material_other-article.pdf',
        'campaign_material_other-essay.pdf',
        'campaign_material_other-leaflet.pdf',
        'campaign_material_yea-1.png',
    ):
        model.files.append(campaign_material[name])

    session = swissvotes_app.session()
    session.add(model)
    session.flush()

    request: Any = DummyRequest()
    request.app = swissvotes_app
    request.locale = 'de_CH'

    layout = VoteLayout(model, request)
    with patch.object(model, 'search', return_value=model.files):
        results = [r[:4] for r in layout.search_results]
        assert results == [
            (0, 'Brief description Swissvotes', 'French', False),
            (0, 'Full analysis of VOX post-vote poll results', 'German',
             False),
            (1, 'campaign_material_other-leaflet.pdf', '', True),
            (1, 'Perché è una pessima idea.', 'Italian, Rhaeto-Romanic',
             False),
            (1, 'Presseschau', 'German', True),
            (3, 'campaign_material_yea-1.png', '', False)
        ]


def test_layout_vote_details(swissvotes_app: TestApp) -> None:
    request: Any = DummyRequest()
    request.app = swissvotes_app
    model = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )

    layout: DefaultLayout

    # VoteStrengthsLayout
    layout = VoteStrengthsLayout(model, request)
    assert layout.title == _("Voter strengths")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # ... log in as editor
    request.roles = ['editor']
    layout = VoteStrengthsLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = VoteStrengthsLayout(model, request)
    assert layout.editbar_links == []

    # UploadVoteAttachemtsLayout
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.title == _("Manage attachments")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # ... log in as editor
    request.roles = ['editor']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = UploadVoteAttachemtsLayout(model, request)
    assert layout.editbar_links == []

    # DeleteVoteLayout
    layout = DeleteVoteLayout(model, request)
    assert layout.title == _("Delete vote")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # ... log in as editor
    request.roles = ['editor']
    layout = DeleteVoteLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = DeleteVoteLayout(model, request)
    assert layout.editbar_links == []

    # ManageCampaingMaterialYeaLayout
    layout = ManageCampaingMaterialYeaLayout(model, request)
    assert layout.title == _("Graphical campaign material for a Yes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # ... log in as editor
    request.roles = ['editor']
    layout = ManageCampaingMaterialYeaLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = ManageCampaingMaterialYeaLayout(model, request)
    assert layout.editbar_links == []

    # ManageCampaingMaterialNayLayout
    layout = ManageCampaingMaterialNayLayout(model, request)
    assert layout.title == _("Graphical campaign material for a No")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # ... log in as editor
    request.roles = ['editor']
    layout = ManageCampaingMaterialNayLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = ManageCampaingMaterialNayLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as editor
    request.roles = ['editor']
    layout = VoteCampaignMaterialLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = VoteCampaignMaterialLayout(model, request)
    assert layout.editbar_links == []


def test_layout_vote_campaign_material(swissvotes_app: TestApp) -> None:
    request: Any = DummyRequest()
    request.app = swissvotes_app
    model = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )

    layout = VoteCampaignMaterialLayout(model, request)
    assert layout.title == _("Documents from the campaign")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )
    assert layout.codes == {
        'doctype': {
            'argument': 'Collection of arguments',
            'letter': 'Letter',
            'documentation': 'Documentation',
            'leaflet': 'Pamphlet',
            'release': 'Media release',
            'memberships': 'List of members',
            'article': 'Press article',
            'legal': 'Legal text',
            'lecture': 'Text of a presentation',
            'statistics': 'Statistical data',
            'other': 'Other',
            'website': 'Website'
        },
        'language': {
            'de': 'German',
            'fr': 'French',
            'it': 'Italian',
            'rm': 'Rhaeto-Romanic',
            'en': 'English',
            'mixed': 'Mixed',
            'other': 'Other'
        },
        'position': {
            'yes': 'Yes',
            'no': 'No',
            'neutral': 'Neutral',
            'mixed': 'Mixed'
        }
    }
    assert layout.format_code(None, None) == ''  # type: ignore[arg-type]
    assert layout.format_code({}, None) == ''  # type: ignore[arg-type]
    assert layout.format_code({}, 'language') == ''
    assert layout.format_code({'language': 'de'}, 'language') == 'German'
    assert layout.format_code({'language': 'zu'}, 'language') == ''
    assert layout.format_code({'language': ['de', 'en']}, 'language') == (
        'German, English'
    )
    assert layout.format_code({'language': ['de', 'fr']}, 'language') == (
        'German, French'
    )
    assert layout.format_partial_date(None) == ''
    assert layout.format_partial_date({}) == ''
    assert layout.format_partial_date({'date_year': 1988}) == '1988'
    assert layout.format_partial_date({'date_year': 1988,
                                       'date_month': 10}) == '10.1988'
    assert layout.format_partial_date({'date_year': 1988,
                                       'date_month': 10,
                                       'date_day': 22}) == '22.10.1988'
    assert layout.format_partial_date({'date_year': 1988,
                                       'date_day': 22}) == '1988'
    assert layout.format_partial_date({'date_month': 10,
                                       'date_day': 22}) == ''
    assert layout.format_partial_date({'date_month': 10}) == ''
    assert layout.format_partial_date({'date_day': 22}) == ''

    assert layout.format_sortable_date(None) == ''
    assert layout.format_sortable_date({}) == ''
    assert layout.format_sortable_date({'date_year': 1988}) == '19880101'
    assert layout.format_sortable_date({'date_year': 1988,
                                        'date_month': 10}) == '19881001'
    assert layout.format_sortable_date({'date_year': 1988,
                                        'date_month': 10,
                                        'date_day': 22}) == '19881022'
    assert layout.format_sortable_date({'date_year': 1988,
                                        'date_day': 22}) == '19880122'
    assert layout.format_sortable_date({'date_month': 10,
                                        'date_day': 22}) == ''
    assert layout.format_sortable_date({'date_month': 10}) == ''
    assert layout.format_sortable_date({'date_day': 22}) == ''

    assert layout.metadata(None) == {}
    assert layout.metadata('aaa') == {}

    model.campaign_material_metadata = {}
    assert layout.metadata(None) == {}
    assert layout.metadata('aaa') == {}

    model.campaign_material_metadata = {
        'xxx': None,
        'yyy.pdf': {},
        'zzz': {'author': 'AAA'}
    }
    assert layout.metadata(None) == {}
    assert layout.metadata('aaa') == {}
    assert layout.metadata('xxx') == {}
    assert layout.metadata('xxx.pdf') == {}
    assert layout.metadata('yyy') == {}
    assert layout.metadata('yyy.pdf') == {}
    assert layout.metadata('zzz') == {
        'title': 'zzz', 'author': 'AAA', 'editor': '', 'date': '',
        'date_sortable': '', 'position': '', 'language': '', 'doctype': '',
        'order': 999, 'protected': False
    }
    assert layout.metadata('zzz.pdf') == {
        'title': 'zzz', 'author': 'AAA', 'editor': '', 'date': '',
        'date_sortable': '', 'position': '', 'language': '', 'doctype': '',
        'order': 999, 'protected': False
    }

    model.campaign_material_metadata = {
        'xxx': {
            'author': 'AAA',
            'editor': 'BBB',
            'date_year': 1988,
            'date_month': 12,
            'date_day': 31,
            'position': 'yes',
            'language': ['de', 'fr'],
            'doctype': ['leaflet', 'article'],
        }
    }
    assert layout.metadata('xxx') == {
        'author': 'AAA',
        'date': '31.12.1988',
        'date_sortable': '19881231',
        'doctype': 'Pamphlet, Press article',
        'editor': 'BBB',
        'language': 'German, French',
        'order': 0,
        'position': 'Yes',
        'title': 'xxx',
        'protected': True
    }


def test_layout_votes(swissvotes_app: TestApp) -> None:
    request: Any = DummyRequest()
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
        'SwissVoteCollection/update-metadata',
        'SwissVoteCollection/update-external-resources',
        'SwissVoteCollection/csv',
        'SwissVoteCollection/xlsx',
    ]

    # Log in as admin
    request.roles = ['admin']
    layout = VotesLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'SwissVoteCollection/update',
        'SwissVoteCollection/update-metadata',
        'SwissVoteCollection/update-external-resources',
        'SwissVoteCollection/csv',
        'SwissVoteCollection/xlsx',
        'SwissVoteCollection/delete',
    ]


def test_layout_votes_details(swissvotes_app: TestApp) -> None:
    # UpdateVotesLayout
    request: Any = DummyRequest()
    request.app = swissvotes_app
    model = SwissVoteCollection(swissvotes_app)

    layout: DefaultLayout
    layout = UpdateVotesLayout(model, request)
    assert layout.title == _("Update dataset on the votes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    # ... log in as editor
    request.roles = ['editor']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = UpdateVotesLayout(model, request)
    assert layout.editbar_links == []

    # UpdateMetadataLayout
    layout = UpdateMetadataLayout(model, request)
    assert layout.title == _('Update metadata on the campaign material')
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    # ... log in as editor
    request.roles = ['editor']
    layout = UpdateMetadataLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = UpdateMetadataLayout(model, request)
    assert layout.editbar_links == []

    # UpdateExternalResourcesLayout
    layout = UpdateExternalResourcesLayout(model, request)
    assert layout.title == _('Update external sources for images')
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    # ... log in as editor
    request.roles = ['editor']
    layout = UpdateExternalResourcesLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = UpdateExternalResourcesLayout(model, request)
    assert layout.editbar_links == []

    # DeleteVotesLayout
    layout = DeleteVotesLayout(model, request)
    assert layout.title == _("Delete all votes")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal/SwissVoteCollection/#'

    # ... log in as editor
    request.roles = ['editor']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []

    # ... log in as admin
    request.roles = ['admin']
    layout = DeleteVotesLayout(model, request)
    assert layout.editbar_links == []


def test_layout_delete_vote_attachment(
    swissvotes_app: TestApp,
    attachments: dict[str, SwissVoteFile]
) -> None:

    request: Any = DummyRequest()
    request.app = swissvotes_app
    vote = SwissVote(
        title_de="Vote",
        title_fr="Vote",
        short_title_de="Vote",
        short_title_fr="Vote",
        bfs_number=Decimal('100')
    )
    model = vote.ad_analysis = attachments['ad_analysis']

    layout = DeleteVoteAttachmentLayout(model, request)
    assert layout.title == _("Delete attachment")
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'Principal/SwissVoteCollection/SwissVote/100/#'
    )

    # Log in as editor
    request.roles = ['editor']
    layout = DeleteVoteAttachmentLayout(model, request)
    assert layout.editbar_links == []

    # Log in as admin
    request.roles = ['admin']
    layout = DeleteVoteAttachmentLayout(model, request)
    assert layout.editbar_links == []
