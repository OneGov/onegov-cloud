from __future__ import annotations

from cgi import FieldStorage
from datetime import date
from decimal import Decimal
from io import BytesIO
from markupsafe import Markup
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.forms import AttachmentsForm
from onegov.swissvotes.forms import PageForm
from onegov.swissvotes.forms import SearchForm
from onegov.swissvotes.forms import UpdateDatasetForm
from onegov.swissvotes.forms import UpdateExternalResourcesForm
from onegov.swissvotes.forms import UpdateMetadataForm
from onegov.swissvotes.models import ColumnMapperDataset
from onegov.swissvotes.models import ColumnMapperMetadata
from onegov.swissvotes.models import TranslatablePage
from tests.shared.utils import use_locale
from xlsxwriter.workbook import Workbook


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.models import SwissVoteFile
    from sqlalchemy.orm import Session
    from webob.multidict import MultiDict
    from .conftest import TestApp

    DummyPostDataBase = MultiDict[str, Any]
else:
    DummyPostDataBase = dict


class DummyPrincipal:
    pass


class DummyApp:
    def __init__(
        self,
        session: Session,
        principal: DummyPrincipal | None,
        mfg_api_token: str | None = None,
        bs_api_token: str | None = None
    ) -> None:
        self._session = session
        self.principal = principal
        self.mfg_api_token = None
        self.bs_api_token = None

    def session(self) -> Session:
        return self._session


class DummyRequest:
    def __init__(
        self,
        session: Session,
        principal: DummyPrincipal | None = None,
        private: bool = False,
        secret: bool = False
    ) -> None:
        self.app = DummyApp(session, principal)
        self.session = session
        self.private = private
        self.secret = secret
        self.locale = 'de_CH'
        self.time_zone = 'Europe/Zurich'

    def is_private(self, model: object) -> bool:
        return self.private

    def is_secret(self, model: object) -> bool:
        return self.secret

    def include(self, resource: object) -> None:
        pass

    def translate(self, text: Any) -> str:
        return text.interpolate()


class DummyPostData(DummyPostDataBase):
    def getlist(self, key: str) -> list[Any]:
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_attachments_form(
    swissvotes_app: TestApp,
    attachments: dict[str, SwissVoteFile]
) -> None:
    session = swissvotes_app.session()
    names = list(attachments.keys())

    # Test apply / update
    votes = SwissVoteCollection(swissvotes_app)
    vote = votes.add(
        id=1,
        bfs_number=Decimal('1'),
        date=date(1990, 6, 2),
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="V D",
        short_title_fr="V F",
        _legal_form=1,
    )

    form = AttachmentsForm()
    form.request = DummyRequest(session, DummyPrincipal())  # type: ignore[assignment]

    # ... empty
    form.apply_model(vote)

    assert all(getattr(form, name).data is None for name in names)

    form.update_model(vote)

    assert all(getattr(vote, name) is None for name in names)

    # ... add attachments (de_CH)
    for name, attachment in attachments.items():
        setattr(vote, name, attachment)
        session.flush()

    # ... not present with fr_CH
    with use_locale(vote, 'fr_CH'):
        form.apply_model(vote)
        assert all(getattr(form, name).data is None for name in names)

    # ... present with de_CH
    form.apply_model(vote)
    for name in names:
        data = getattr(form, name).data
        assert data['size']
        assert data['filename'] == name
        assert data['mimetype'] in (
            'text/plain',
            'text/csv',
            'application/pdf',
            'application/zip',
            'application/vnd.ms-office',
            'application/octet-stream',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    form.update_model(vote)

    for name in names:
        file = getattr(vote, name)
        assert file == attachments[name]
        assert file.reference.filename == name
        assert file.reference.content_type in (
            'text/plain',
            'text/csv',
            'application/pdf',
            'application/zip',
            'application/vnd.ms-office',
            'application/octet-stream',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # ... replace all de_CH
    for name in names:
        field_storage = FieldStorage()
        field_storage.file = BytesIO(f'{name}-1'.encode())
        field_storage.type = 'image/png'  # ignored
        field_storage.filename = f'{name}.png'  # extension removed

        getattr(form, name).process(DummyPostData({name: field_storage}))

    form.update_model(vote)

    assert all([
        getattr(vote, name).reference.file.read() == f'{name}-1'.encode()
        for name in names
    ])

    # ... add all fr_CH
    with use_locale(vote, 'fr_CH'):
        for name in names:
            field_storage = FieldStorage()
            field_storage.file = BytesIO(f'{name}-fr'.encode())
            field_storage.type = 'image/png'  # ignored
            field_storage.filename = f'{name}.png'  # extension removed

            getattr(form, name).process(DummyPostData({name: field_storage}))

        form.update_model(vote)

        assert all([
            getattr(vote, name).reference.file.read() == f'{name}-fr'.encode()
            for name in names
        ])

        # ... delete all fr_CH
        for name in names:
            getattr(form, name).action = 'delete'

        form.update_model(vote)

        assert all([getattr(vote, name) is None for name in names])

    assert all([getattr(vote, name) is not None for name in names])

    # ... delete all de_CH
    for name in names:
        getattr(form, name).action = 'delete'

    form.update_model(vote)

    assert vote.files == []

    # Test validation
    form = AttachmentsForm()
    assert form.validate()


def test_page_form(session: Session) -> None:
    # Test apply / update
    pages = TranslatablePageCollection(session)
    page = pages.add(
        id='page',
        title_translations={'de_CH': 'Titel', 'en_US': 'Title'},
        content_translations={'de_CH': 'Inhalt', 'en_US': 'Content'},
        show_timeline=False
    )

    form = PageForm()

    # .. de_CH
    form.apply_model(page)
    assert form.title.data == 'Titel'
    assert form.content.data == 'Inhalt'
    assert form.show_timeline.data is False

    form.title.data = 'A'
    form.content.data = Markup('B')
    form.show_timeline.data = True

    form.update_model(page)

    assert page.title_translations == {'de_CH': 'A', 'en_US': 'Title'}
    assert page.content_translations == {'de_CH': 'B', 'en_US': 'Content'}
    assert page.id == 'page'
    assert page.show_timeline is True

    # ... en_US
    with use_locale(page, 'en_US'):
        form.apply_model(page)
        assert form.title.data == 'Title'
        assert form.content.data == 'Content'

        form.title.data = 'C'
        form.content.data = Markup('D')
        form.update_model(page)

    assert page.title_translations == {'de_CH': 'A', 'en_US': 'C'}
    assert page.content_translations == {'de_CH': 'B', 'en_US': 'D'}
    assert page.id == 'page'

    # ... fr_CH
    with use_locale(page, 'fr_CH'):
        form.apply_model(page)
        assert form.title.data == 'A'
        assert form.content.data == 'B'

        form.title.data = 'E'
        form.content.data = Markup('F')
        form.update_model(page)

    assert page.title_translations == {
        'de_CH': 'A', 'en_US': 'C', 'fr_CH': 'E'
    }
    assert page.content_translations == {
        'de_CH': 'B', 'en_US': 'D', 'fr_CH': 'F'
    }
    assert page.id == 'page'

    # Test ID generation
    form = PageForm()
    form.request = DummyRequest(session, DummyPrincipal())  # type: ignore[assignment]

    assert form.id == 'page-1'

    form.title.data = ' Über uns '
    assert form.id == 'uber-uns'

    form.update_model(page)
    assert page.id == 'page'

    page = TranslatablePage()
    form.update_model(page)
    assert page.id == 'uber-uns'

    # Test validation
    form = PageForm()
    assert not form.validate()

    form = PageForm(DummyPostData({'title': 'X', 'content': 'Y'}))
    assert form.validate()


def test_search_form(swissvotes_app: TestApp) -> None:
    # Test on request / popluate
    form = SearchForm()
    form.request = DummyRequest(swissvotes_app.session(), DummyPrincipal())  # type: ignore[assignment]
    form.on_request()

    assert form.legal_form.choices == [
        (1, 'Mandatory referendum'),
        (2, 'Optional referendum'),
        (3, 'Popular initiative'),
        (4, 'Direct counter-proposal'),
        (5, 'Tie-breaker'),
    ]
    assert form.result.choices == [
        (0, 'Rejected'),
        (1, 'Accepted')
    ]
    assert form.position_federal_council.choices == [
        (1, 'Accepting'),
        (2, 'Rejecting'),
        (3, 'None'),
        (-1, 'Missing'),
    ]
    assert form.position_national_council.choices == [
        (1, 'Accepting'),
        (2, 'Rejecting'),
        (3, 'None'),
    ]
    assert form.position_council_of_states.choices == [
        (1, 'Accepting'),
        (2, 'Rejecting'),
        (3, 'None'),
    ]
    assert form.policy_area.choices == []

    # ... descriptors available
    votes = SwissVoteCollection(swissvotes_app)
    kwargs = {
        'date': date(1990, 6, 2),
        'title_de': "Vote DE",
        'title_fr': "Vote FR",
        'short_title_de': "V D",
        'short_title_fr': "V F",
        '_legal_form': 1,
    }
    votes.add(
        id=1,
        bfs_number=Decimal('1'),
        descriptor_1_level_1=Decimal('4'),
        descriptor_1_level_2=Decimal('4.2'),
        descriptor_1_level_3=Decimal('4.21'),
        descriptor_2_level_1=Decimal('10'),
        descriptor_2_level_2=Decimal('10.3'),
        descriptor_2_level_3=Decimal('10.35'),
        descriptor_3_level_1=Decimal('10'),
        descriptor_3_level_2=Decimal('10.3'),
        descriptor_3_level_3=Decimal('10.33'),
        **kwargs
    )
    votes.add(
        id=2,
        bfs_number=Decimal('3'),
        descriptor_1_level_1=Decimal('8'),
        descriptor_2_level_1=Decimal('7'),
        descriptor_2_level_2=Decimal('7.5'),
        descriptor_3_level_1=Decimal('9'),
        descriptor_3_level_2=Decimal('9.3'),
        descriptor_3_level_3=Decimal('9.39'),
        **kwargs
    )
    votes.add(
        id=3,
        bfs_number=Decimal('3'),
        descriptor_1_level_1=Decimal('8'),
        descriptor_1_level_2=Decimal('8.7'),
        descriptor_2_level_1=Decimal('6'),
        descriptor_2_level_2=Decimal('6.1'),
        descriptor_2_level_3=Decimal('6.14'),
        **kwargs
    )

    form.on_request()
    assert form.policy_area.choices == [
        ('4', 'd-1-4'),
        ('4.42', 'd-2-42'),
        ('4.42.421', 'd-3-421'),
        ('6', 'd-1-6'),
        ('6.61', 'd-2-61'),
        ('6.61.614', 'd-3-614'),
        ('7', 'd-1-7'),
        ('7.75', 'd-2-75'),
        ('8', 'd-1-8'),
        ('8.87', 'd-2-87'),
        ('9', 'd-1-9'),
        ('9.93', 'd-2-93'),
        ('10', 'd-1-10'),
        ('10.103', 'd-2-103'),
        ('10.103.1033', 'd-3-1033'),
        ('10.103.1035', 'd-3-1035')
    ]

    # Test apply
    form.apply_model(votes)
    assert form.from_date.data is None
    assert form.to_date.data is None
    assert form.legal_form.data == [1, 2, 3, 4, 5]
    assert form.result.data == [0, 1]
    assert form.policy_area.data is None
    assert form.term.data is None
    assert form.full_text.data == 1
    assert form.position_federal_council.data == [1, 2, 3, -1]
    assert form.position_national_council.data == [1, 2, 3]
    assert form.position_council_of_states.data == [1, 2, 3]
    assert form.sort_by.data is None
    assert form.sort_order.data is None

    votes.from_date = date(2010, 1, 1)
    votes.to_date = date(2010, 12, 31)
    votes.legal_form = [1, 2]
    votes.result = [0]
    votes.policy_area = ['6', '7.75', '10.103.1035']
    votes.term = 'term'
    votes.full_text = False
    votes.position_federal_council = [2, 3]
    votes.position_national_council = [3]
    votes.position_council_of_states = [3, 1, 2]
    votes.sort_by = 'title'
    votes.sort_order = 'ascending'

    form.apply_model(votes)

    assert form.from_date.data == date(2010, 1, 1)
    assert form.to_date.data == date(2010, 12, 31)
    assert form.legal_form.data == [1, 2]
    assert form.result.data == [0]
    assert form.policy_area.data == ['6', '7.75', '10.103.1035']
    assert form.term.data == 'term'
    assert form.full_text.data == 0
    assert form.position_federal_council.data == [2, 3]
    assert form.position_national_council.data == [3]
    assert form.position_council_of_states.data == [3, 1, 2]
    assert form.sort_by.data == 'title'
    assert form.sort_order.data == 'ascending'

    # Test validation
    form = SearchForm()
    assert form.validate()


def test_update_dataset_form(session: Session) -> None:
    request: Any = DummyRequest(session, DummyPrincipal())

    # Validate
    form = UpdateDatasetForm()
    form.request = request
    assert not form.validate()

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    worksheet.write_row(0, 0, ColumnMapperDataset().columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # anr / NUMERIC
        '1.2.2008',  # datum / DATE
        'titel_kurz_d',  # short_title_de / TEXT
        'titel_kurz_f',  # short_title_fr / TEXT
        'titel_kurz_e',  # short_title_en / TEXT
        'titel_off_d',  # title_de / TEXT
        'titel_off_f',  # title_fr / TEXT
        'stichwort',  # stichwort / TEXT
        '3',  # rechtsform / INTEGER
        '',  # anneepolitique / TEXT
        '',  # bkchrono-de / TEXT
        '',  # bkchrono-fr / TEXT
        '13',  # d1e1 / NUMERIC
        '',  # d1e2 / NUMERIC
        '',  # d1e3 / NUMERIC
        '12',  # d2e1 / NUMERIC
        '12.6',  # d2e2 / NUMERIC
        '',  # d2e3 / NUMERIC
        '12',  # d3e1 / NUMERIC
        '12.5',  # d3e2 / NUMERIC
        '12.55',  # d3e3 / NUMERIC
        '',  # br-pos
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.file = file
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    form.dataset.process(DummyPostData({'dataset': field_storage}))

    assert form.validate()


def test_update_metadata_form(session: Session) -> None:
    request: Any = DummyRequest(session, DummyPrincipal())

    # Validate
    form = UpdateMetadataForm()
    form.request = request
    assert not form.validate()

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('Metadaten zu Scans')
    worksheet.write_row(0, 0, ColumnMapperMetadata().columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # Abst-Nummer
        'letter.pdf',  # Dateiname
        'Brief',  # Titel des Dokuments
        'Ja',  # Position zur Vorlage
        'Autor',  # AutorIn (Nachname Vorname) des Dokuments
        'Herausgeber',  # AuftraggeberIn/HerausgeberIn des Dokuments
        '1970',  # Datum Jahr
        '12',  # Datum Monat
        '31',  # Datum Tag
        'x',  # Sprache D
        'x',  # Sprache E
        'x',  # Sprache F
        'x',  # Sprache IT
        'x',  # Sprache RR
        'x',  # Sprache Gemischt
        'x',  # Doktyp Argumentarium
        'x',  # Doktyp Presseartikel
        'x',  # Doktyp Medienmitteilung
        'x',  # Doktyp Referatstext
        'x',  # Doktyp Flugblatt
        'x',  # Doktyp Abhandlung
        'x',  # Doktyp Brief
        'x',  # Doktyp Rechtstext
        'x',  # Doktyp Anderes
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.file = file
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    form.metadata.process(DummyPostData({'metadata': field_storage}))

    assert form.validate()


def test_update_external_resources_form(session: Session) -> None:
    form = UpdateExternalResourcesForm()
    form.request = DummyRequest(session, DummyPrincipal())  # type: ignore[assignment]

    assert form.resources.choices == [
        ('mfg', 'eMuseum.ch'),
        ('bs', 'Plakatsammlung Basel'),
        ('sa', 'Social Archives')
    ]

    # Validate
    assert not form.validate()

    form.resources.process(DummyPostData({'resources': ['sa']}))
    assert form.validate()

    form.resources.process(DummyPostData({'resources': ['bs']}))
    assert not form.validate()  # missing API token

    form.resources.process(DummyPostData({'resources': ['mfg']}))
    assert not form.validate()  # missing API token

    form.request.app.mfg_api_token = 'token-mfg'
    form.request.app.bs_api_token = 'token-bs'
    form.resources.process(DummyPostData({'resources': ['sa', 'bs', 'mfg']}))
    assert form.validate()
