from cgi import FieldStorage
from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.collections import TranslatablePageCollection
from onegov.swissvotes.forms import AttachmentsForm
from onegov.swissvotes.forms import PageForm
from onegov.swissvotes.forms import SearchForm
from onegov.swissvotes.forms import UpdateDatasetForm
from onegov.swissvotes.models import ColumnMapper
from onegov.swissvotes.models import TranslatablePage
from psycopg2.extras import NumericRange
from xlsxwriter.workbook import Workbook


class DummyPrincipal(object):
    pass


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session, principal=None, private=False, secret=False):
        self.app = DummyApp(session, principal)
        self.session = session
        self.private = private
        self.secret = secret
        self.locale = 'de_CH'
        self.time_zone = 'Europe/Zurich'

    def is_private(self, model):
        return self.private

    def is_secret(self, model):
        return self.secret

    def include(self, resource):
        pass

    def translate(self, text):
        return text.interpolate()


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_attachments_form(swissvotes_app, attachments):
    session = swissvotes_app.session()
    names = list(attachments.keys())

    # Test apply / update
    votes = SwissVoteCollection(swissvotes_app)
    vote = votes.add(
        id=1,
        bfs_number=Decimal('1'),
        date=date(1990, 6, 2),
        legislation_number=4,
        legislation_decade=NumericRange(1990, 1994),
        title_de="Vote DE",
        title_fr="Vote FR",
        short_title_de="V D",
        short_title_fr="V F",
        votes_on_same_day=2,
        _legal_form=1,
    )

    form = AttachmentsForm()
    form.request = DummyRequest(session, DummyPrincipal())

    # ... empty
    form.apply_model(vote)

    assert all([getattr(form, name).data is None for name in names])

    form.update_model(vote)

    assert all([getattr(vote, name) is None for name in names])

    # ... add attachments (de_CH)
    for name, attachment in attachments.items():
        setattr(vote, name, attachment)
        session.flush()

    # ... not present with fr_CH
    vote.session_manager.current_locale = 'fr_CH'

    form.apply_model(vote)

    assert all([getattr(form, name).data is None for name in names])

    # ... present with de_CH
    vote.session_manager.current_locale = 'de_CH'

    form.apply_model(vote)

    for name in names:
        data = getattr(form, name).data
        assert data['size']
        assert data['filename'] == name
        assert data['mimetype'] in (
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
    vote.session_manager.current_locale = 'fr_CH'

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

    vote.session_manager.current_locale = 'de_CH'

    assert all([getattr(vote, name) is not None for name in names])

    # ... delete all de_CH
    for name in names:
        getattr(form, name).action = 'delete'

    form.update_model(vote)

    assert vote.files == []

    # Test validation
    form = AttachmentsForm()
    assert form.validate()


def test_page_form(session):
    # Test apply / update
    pages = TranslatablePageCollection(session)
    page = pages.add(
        id='page',
        title_translations={'de_CH': 'Titel', 'en_US': 'Title'},
        content_translations={'de_CH': 'Inhalt', 'en_US': 'Content'},
    )

    form = PageForm()

    # .. de_CH
    form.apply_model(page)
    assert form.title.data == 'Titel'
    assert form.content.data == 'Inhalt'

    form.title.data = 'A'
    form.content.data = 'B'

    form.update_model(page)

    assert page.title_translations == {'de_CH': 'A', 'en_US': 'Title'}
    assert page.content_translations == {'de_CH': 'B', 'en_US': 'Content'}
    assert page.id == 'page'

    # ... en_US
    page.session_manager.current_locale = 'en_US'

    form.apply_model(page)
    assert form.title.data == 'Title'
    assert form.content.data == 'Content'

    form.title.data = 'C'
    form.content.data = 'D'

    form.update_model(page)

    assert page.title_translations == {'de_CH': 'A', 'en_US': 'C'}
    assert page.content_translations == {'de_CH': 'B', 'en_US': 'D'}
    assert page.id == 'page'

    # ... fr_CH
    page.session_manager.current_locale = 'fr_CH'

    form.apply_model(page)
    assert form.title.data == 'A'
    assert form.content.data == 'B'

    form.title.data = 'E'
    form.content.data = 'F'

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
    form.request = DummyRequest(session, DummyPrincipal())

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


def test_search_form(swissvotes_app):
    # Test on request / popluate
    form = SearchForm()
    form.request = DummyRequest(swissvotes_app.session(), DummyPrincipal())
    form.on_request()

    assert form.legal_form.choices == [
        (1, 'Mandatory referendum'),
        (2, 'Optional referendum'),
        (3, 'Popular initiative'),
        (4, 'Direct counter-proposal')
    ]
    assert form.result.choices == [
        (0, 'Rejected'),
        (1, 'Accepted')
    ]
    assert form.position_federal_council.choices == [
        (1, 'Accepting'),
        (2, 'Rejecting'),
        (3, 'Neutral'),
        (-1, 'Without / Unknown')
    ]
    assert form.position_national_council.choices == [
        (1, 'Accepting'),
        (2, 'Rejecting'),
        (-1, 'Without / Unknown')
    ]
    assert form.position_council_of_states.choices == [
        (1, 'Accepting'),
        (2, 'Rejecting'),
        (-1, 'Without / Unknown')
    ]
    assert form.policy_area.choices == []

    # ... descriptors available
    votes = SwissVoteCollection(swissvotes_app)
    kwargs = {
        'date': date(1990, 6, 2),
        'legislation_number': 4,
        'legislation_decade': NumericRange(1990, 1994),
        'title_de': "Vote DE",
        'title_fr': "Vote FR",
        'short_title_de': "V D",
        'short_title_fr': "V F",
        'votes_on_same_day': 2,
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
    assert form.legal_form.data == [1, 2, 3, 4]
    assert form.result.data == [0, 1]
    assert form.policy_area.data is None
    assert form.term.data is None
    assert form.full_text.data == 1
    assert form.position_federal_council.data == [1, 2, 3, -1]
    assert form.position_national_council.data == [1, 2, -1]
    assert form.position_council_of_states.data == [1, 2, - 1]
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
    votes.position_national_council = [-1]
    votes.position_council_of_states = [-1, 1, 2]
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
    assert form.position_national_council.data == [-1]
    assert form.position_council_of_states.data == [-1, 1, 2]
    assert form.sort_by.data == 'title'
    assert form.sort_order.data == 'ascending'

    # Test validation
    form = SearchForm()
    assert form.validate()


def test_update_dataset_form(session):
    request = DummyRequest(session, DummyPrincipal())

    # Validate
    form = UpdateDatasetForm()
    form.request = request
    assert not form.validate()

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet()
    worksheet.write_row(0, 0, ColumnMapper().columns.values())
    worksheet.write_row(1, 0, [
        100.1,  # anr / NUMERIC
        '1.2.2008',  # datum / DATE
        1,  # legislatur / INTEGER
        '2004-2008',  # legisjahr / INT4RANGE
        'kurztitel de',  # titel_kurz_d
        'kurztitel fr',  # titel_kurz_f
        'titel de',  # titel_off_d
        'titel fr',  # titel_off_f
        'stichwort',  # stichwort / TEXT
        2,  # anzahl / INTEGER
        3,  # rechtsform
    ])
    workbook.close()
    file.seek(0)

    field_storage = FieldStorage()
    field_storage.file = file
    field_storage.type = 'application/excel'
    field_storage.filename = 'test.xlsx'

    form.dataset.process(DummyPostData({'dataset': field_storage}))

    assert form.validate()
