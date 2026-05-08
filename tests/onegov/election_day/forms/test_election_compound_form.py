from __future__ import annotations

from cgi import FieldStorage
from datetime import date
from io import BytesIO
from onegov.election_day.forms import ElectionCompoundForm
from onegov.election_day.models import Canton
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def test_election_compound_form_on_request(session: Session) -> None:
    session.add(
        ProporzElection(
            title='r1',
            domain='region',
            shortcode='2',
            date=date(2001, 1, 1))
    )
    session.add(
        ProporzElection(
            title='d1',
            domain='district',
            shortcode='1',
            date=date(2001, 1, 1))
    )
    session.add(
        ProporzElection(
            title='m1',
            domain='municipality',
            date=date(2000, 1, 1))
    )
    session.add(
        Election(
            title='m2',
            domain='municipality',
            date=date(2000, 1, 1))
    )
    session.add(
        ProporzElection(
            title='f1',
            domain='federation',
            date=date(2001, 1, 1))
    )
    session.flush()

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='zg', canton='zg')  # type: ignore[misc]
    form.on_request()
    assert [x[0] for x in form.domain_elections.choices] == ['municipality']
    assert [x[0] for x in form.region_elections.choices] == ['r1']
    assert [x[0] for x in form.district_elections.choices] == ['d1']
    assert [x[0] for x in form.municipality_elections.choices] == ['m1']
    assert isinstance(form.title_de.validators[0], InputRequired)
    assert form.title_fr.validators == []
    assert form.title_it.validators == []
    assert form.title_rm.validators == []

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.default_locale = 'fr_CH'
    form.request.app.principal = Canton(name='gr', canton='gr')  # type: ignore[misc]
    form.on_request()
    assert [x[0] for x in form.domain_elections.choices] == [
        'region', 'district', 'municipality'
    ]
    assert [x[0] for x in form.region_elections.choices] == ['r1']
    assert [x[0] for x in form.district_elections.choices] == ['d1']
    assert [x[0] for x in form.municipality_elections.choices] == ['m1']
    assert form.title_de.validators == []
    assert isinstance(form.title_fr.validators[0], InputRequired)
    assert form.title_it.validators == []
    assert form.title_rm.validators == []


def test_election_compound_form_validate(session: Session) -> None:
    model = ElectionCompound(
        id='elections',
        title='Elections',
        domain='federation',
        date=date(2015, 6, 14)
    )
    session.add(model)
    session.add(
        ElectionCompound(
            id='elections-copy',
            external_id='ext-1',
            title='Elections',
            domain='federation',
            date=date(2015, 6, 14)
        )
    )
    session.add(
        ProporzElection(
            title='election-1',
            external_id='ext-2',
            domain='district',
            date=date(2001, 1, 1))
    )
    session.add(
        ProporzElection(
            title='election-2',
            domain='district',
            date=date(2001, 1, 1))
    )
    session.flush()

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')  # type: ignore[misc]
    form.on_request()
    form.apply_model(model)
    assert form.id.data == 'elections'
    assert not form.validate()
    assert form.errors == {
        'date': ['This field is required.'],
        'district_elections': ['This field is required.'],
        'domain': ['This field is required.'],
        'domain_elections': ['This field is required.'],
        'title_de': ['This field is required.'],
        'id': ['This field is required.']
    }

    form = ElectionCompoundForm(DummyPostData({'id': 'elections copy'}))
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')  # type: ignore[misc]
    form.on_request()
    form.model = model
    assert not form.validate()
    assert form.errors['id'] == ['Invalid ID']

    form = ElectionCompoundForm(
        DummyPostData({'id': 'elections-copy', 'external_id': 'ext-1'})
    )
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')  # type: ignore[misc]
    form.on_request()
    form.model = model
    assert not form.validate()
    assert form.errors['id'] == ['ID already exists']
    assert form.errors['external_id'] == ['ID already exists']

    form = ElectionCompoundForm(DummyPostData({'external_id': 'ext-2'}))
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')  # type: ignore[misc]
    form.on_request()
    form.model = model
    assert not form.validate()
    assert form.errors['external_id'] == ['ID already exists']

    form = ElectionCompoundForm(DummyPostData({
        'date': '2012-01-01',
        'domain_elections': 'district',
        'domain': 'canton',
        'title_de': 'Elections',
        'id': 'elections-new',
        'district_elections': ['election-1']
    }))
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')  # type: ignore[misc]
    form.on_request()
    form.model = model
    assert form.validate()
    form.update_model(model)
    session.flush()
    assert session.query(ElectionCompound).filter_by(id='elections-new').one()

    form.process(DummyPostData({
        'date': '2012-01-01',
        'domain_elections': 'district',
        'domain': 'canton',
        'title_de': 'Elections',
        'id': 'elections-new',
        'district_elections': ['election-1', 'election-2']
    }))
    assert form.validate()


def test_election_compound_form_model(
    election_day_app_zg: TestApp,
    related_link_labels: dict[str, str],
    explanations_pdf: BytesIO,
    upper_apportionment_pdf: BytesIO,
    lower_apportionment_pdf: BytesIO
) -> None:

    session = election_day_app_zg.session()

    date_ = date(2001, 1, 1)
    e_r = Election(domain='region', title='e', id='e-r', date=date_)
    e_d = Election(domain='district', title='e', id='e-d', date=date_)
    e_m = Election(domain='municipality', title='e', id='e-m', date=date_)
    session.add(e_r)
    session.add(e_d)
    session.add(e_m)
    session.flush()

    model = ElectionCompound()
    model.id = 'elections'
    model.external_id = '120'
    model.title = 'Elections (DE)'
    model.title_translations = {
        'de_CH': 'Elections (DE)',
        'fr_CH': 'Elections (FR)',
        'it_CH': 'Elections (IT)',
        'rm_CH': 'Elections (RM)',
    }
    model.short_title_translations = {
        'de_CH': 'E_DE',
        'fr_CH': 'E_FR',
        'it_CH': 'E_IT',
        'rm_CH': 'E_RM',
    }
    model.date = date(2012, 1, 1)
    model.domain = 'canton'
    model.domain_elections = 'region'
    model.shortcode = 'xy'
    model.related_link = 'http://u.rl'
    model.related_link_label = related_link_labels
    model.explanations_pdf = (explanations_pdf, 'e.pdf')
    model.upper_apportionment_pdf = (upper_apportionment_pdf, 'u.pdf')
    model.lower_apportionment_pdf = (lower_apportionment_pdf, 'l.pdf')
    model.show_seat_allocation = True
    model.show_list_groups = True
    model.show_party_strengths = True
    model.show_party_panachage = True
    model.elections = [e_r]
    model.pukelsheim = True
    model.completes_manually = True
    model.manually_completed = True
    model.voters_counts = True
    model.exact_voters_counts = True
    model.horizontal_party_strengths = True
    model.use_historical_party_results = True
    model.colors = {
        'FDP': '#3a8bc1',
        'CVP': '#ff9100',
    }
    session.add(model)

    form = ElectionCompoundForm()
    form.apply_model(model)
    assert form.id.data == 'elections'
    assert form.external_id.data == '120'
    assert form.title_de.data == 'Elections (DE)'
    assert form.title_fr.data == 'Elections (FR)'
    assert form.title_it.data == 'Elections (IT)'
    assert form.title_rm.data == 'Elections (RM)'
    assert form.short_title_de.data == 'E_DE'
    assert form.short_title_fr.data == 'E_FR'
    assert form.short_title_it.data == 'E_IT'
    assert form.short_title_rm.data == 'E_RM'
    assert form.date.data == date(2012, 1, 1)
    assert form.domain.data == 'canton'
    assert form.domain_elections.data == 'region'
    assert form.shortcode.data == 'xy'
    assert form.related_link.data == 'http://u.rl'
    assert form.related_link_label_de.data == 'DE'
    assert form.related_link_label_fr.data == 'FR'
    assert form.related_link_label_it.data == 'IT'
    assert form.related_link_label_rm.data == 'RM'
    assert form.explanations_pdf.data['mimetype'] == 'application/pdf'  # type: ignore[index]
    assert form.upper_apportionment_pdf.data['mimetype'] == 'application/pdf'  # type: ignore[index]
    assert form.lower_apportionment_pdf.data['mimetype'] == 'application/pdf'  # type: ignore[index]
    assert form.show_seat_allocation.data is True
    assert form.show_list_groups.data is True
    assert form.show_party_strengths.data is True
    assert form.show_party_panachage.data is True
    assert form.region_elections.data == ['e-r']
    assert form.district_elections.data == []
    assert form.municipality_elections.data == []
    assert form.pukelsheim.data is True
    assert form.completes_manually.data is True
    assert form.manually_completed.data is True
    assert form.voters_counts.data is True
    assert form.exact_voters_counts.data is True
    assert form.horizontal_party_strengths.data is True
    assert form.use_historical_party_results.data is True
    assert form.colors.data == (
        'CVP #ff9100\n'
        'FDP #3a8bc1'
    )

    form.id.data = 'some-elections'
    form.external_id.data = '140'
    form.title_de.data = 'Some Elections (DE)'
    form.title_fr.data = 'Some Elections (FR)'
    form.title_it.data = 'Some Elections (IT)'
    form.title_rm.data = 'Some Elections (RM)'
    form.short_title_de.data = 'ED'
    form.short_title_fr.data = 'EF'
    form.short_title_it.data = 'EI'
    form.short_title_rm.data = 'ER'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.domain_elections.data = 'district'
    form.shortcode.data = 'yz'
    form.related_link.data = 'http://ur.l'
    form.explanations_pdf.action = 'delete'
    form.upper_apportionment_pdf.action = 'delete'
    form.lower_apportionment_pdf.action = 'delete'
    form.show_seat_allocation.data = False
    form.show_list_groups.data = False
    form.show_party_strengths.data = False
    form.show_party_panachage.data = False
    form.region_elections.data = ['e-r']
    form.district_elections.data = ['e-d']
    form.municipality_elections.data = ['e-m']
    form.pukelsheim.data = False
    form.completes_manually.data = False
    form.manually_completed.data = False
    form.voters_counts.data = False
    form.exact_voters_counts.data = False
    form.horizontal_party_strengths.data = False
    form.use_historical_party_results.data = False
    form.colors.data = (
        'CVP #ff9100\r\n'
        'SP Juso #dd0e0e\n'
        'FDP   #3a8bc1\n'
        'GLP\t\t#aeca00\n'
    )

    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.app.principal = Canton(name='gr', canton='gr')  # type: ignore[misc]
    form.on_request()
    form.update_model(model)
    # undo mypy narrowing
    model = model
    assert model.id == 'some-elections'
    assert model.external_id == '140'
    assert model.title == 'Some Elections (DE)'
    assert model.title_translations == {
        'de_CH': 'Some Elections (DE)',
        'fr_CH': 'Some Elections (FR)',
        'it_CH': 'Some Elections (IT)',
        'rm_CH': 'Some Elections (RM)',
    }
    assert model.short_title_translations == {
        'de_CH': 'ED',
        'fr_CH': 'EF',
        'it_CH': 'EI',
        'rm_CH': 'ER',
    }
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.domain_elections == 'district'
    assert model.shortcode == 'yz'
    assert model.related_link == 'http://ur.l'
    assert model.explanations_pdf is None
    assert model.upper_apportionment_pdf is None
    assert model.lower_apportionment_pdf is None
    assert model.pukelsheim is False
    assert model.completes_manually is False
    assert model.manually_completed is False
    assert model.voters_counts is False
    assert model.exact_voters_counts is False
    assert model.horizontal_party_strengths is False
    assert model.use_historical_party_results is False
    assert form.show_seat_allocation.data is False
    assert form.show_list_groups.data is False
    assert form.show_party_strengths.data is False
    assert form.show_party_panachage.data is False
    assert sorted([e.id for e in model.elections]) == ['e-d']
    assert model.colors == {
        'CVP': '#ff9100',
        'FDP': '#3a8bc1',
        'GLP': '#aeca00',
        'SP Juso': '#dd0e0e',
    }

    form.domain_elections.data = 'municipality'
    form.update_model(model)
    assert sorted([e.id for e in model.elections]) == ['e-m']

    field_storage = FieldStorage()
    field_storage.file = BytesIO('my-file-e'.encode())
    field_storage.type = 'image/png'  # ignored
    field_storage.filename = 'my-file-e.pdf'
    form.explanations_pdf.process(
        DummyPostData({'explanations_pdf': field_storage})
    )

    field_storage = FieldStorage()
    field_storage.file = BytesIO('my-file-u'.encode())
    field_storage.type = 'image/png'  # ignored
    field_storage.filename = 'my-file-u.pdf'
    form.upper_apportionment_pdf.process(
        DummyPostData({'upper_apportionment_pdf': field_storage})
    )

    field_storage = FieldStorage()
    field_storage.file = BytesIO('my-file-l'.encode())
    field_storage.type = 'image/png'  # ignored
    field_storage.filename = 'my-file-l.pdf'
    form.lower_apportionment_pdf.process(
        DummyPostData({'lower_apportionment_pdf': field_storage})
    )

    form.update_model(model)

    # undo mypy narrowing
    model = model
    assert model.explanations_pdf is not None
    assert model.explanations_pdf.name == 'explanations_pdf'
    assert model.explanations_pdf.reference.filename == 'my-file-e.pdf'
    assert model.explanations_pdf.reference.file.read() == b'my-file-e'

    assert model.upper_apportionment_pdf is not None
    assert model.upper_apportionment_pdf.name == 'upper_apportionment_pdf'
    assert model.upper_apportionment_pdf.reference.filename == 'my-file-u.pdf'
    assert model.upper_apportionment_pdf.reference.file.read() == b'my-file-u'

    assert model.lower_apportionment_pdf is not None
    assert model.lower_apportionment_pdf.name == 'lower_apportionment_pdf'
    assert model.lower_apportionment_pdf.reference.filename == 'my-file-l.pdf'
    assert model.lower_apportionment_pdf.reference.file.read() == b'my-file-l'


def test_election_compound_form_relations(session: Session) -> None:
    session.add(
        ElectionCompound(
            title='First Compound',
            domain='federation',
            date=date(2011, 1, 1),
        )
    )
    session.add(
        ElectionCompound(
            title='Second Compound',
            domain='federation',
            date=date(2011, 1, 2),
        )
    )

    # Add a new election with relations
    compound = ElectionCompound()

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.app.principal = Canton(name='gr', canton='gr')  # type: ignore[misc]
    form.on_request()
    assert form.related_compounds_historical.choices == [
        ('second-compound', '02.01.2011 Second Compound'),
        ('first-compound', '01.01.2011 First Compound'),
    ]
    assert form.related_compounds_other.choices == [
        ('second-compound', '02.01.2011 Second Compound'),
        ('first-compound', '01.01.2011 First Compound'),
    ]

    form.title_de.data = 'Third Compound'
    form.date.data = date(2011, 1, 3)
    form.domain.data = 'federation'
    form.shortcode.data = 'SC'
    form.related_compounds_historical.data = ['first-compound']
    form.related_compounds_other.data = ['first-compound', 'second-compound']
    form.update_model(compound)
    session.add(compound)
    session.flush()

    # Change existing relations of a compound
    compound = session.query(ElectionCompound).filter_by(
        id='first-compound'
    ).one()

    form = ElectionCompoundForm()
    form.request = DummyRequest(session=session)  # type: ignore[assignment]
    form.request.app.principal = Canton(name='gr', canton='gr')  # type: ignore[misc]
    form.on_request()
    assert form.related_compounds_historical.choices == [
        ('third-compound', '03.01.2011 SC Third Compound'),
        ('second-compound', '02.01.2011 Second Compound'),
        ('first-compound', '01.01.2011 First Compound'),
    ]
    assert form.related_compounds_other.choices == [
        ('third-compound', '03.01.2011 SC Third Compound'),
        ('second-compound', '02.01.2011 Second Compound'),
        ('first-compound', '01.01.2011 First Compound'),
    ]
    form.apply_model(compound)
    assert form.related_compounds_historical.data == ['third-compound']
    assert form.related_compounds_other.data == ['third-compound']

    form.related_compounds_historical.data = ['second-compound']
    form.related_compounds_other.data = ['second-compound', 'third-compound']
    form.update_model(compound)
    session.add(compound)
    session.flush()

    # Check all relations
    compound = session.query(ElectionCompound).filter_by(
        id='first-compound'
    ).one()
    form.apply_model(compound)
    assert form.related_compounds_historical.data == ['second-compound']
    assert set(form.related_compounds_other.data) == {
        'second-compound', 'third-compound'
    }

    compound = session.query(ElectionCompound).filter_by(
        id='second-compound'
    ).one()
    form.apply_model(compound)
    assert form.related_compounds_historical.data == ['first-compound']
    assert set(form.related_compounds_other.data) == {
        'first-compound', 'third-compound'
    }

    compound = session.query(ElectionCompound).filter_by(
        id='third-compound'
    ).one()
    form.apply_model(compound)
    assert form.related_compounds_historical.data == []
    assert set(form.related_compounds_other.data) == {
        'first-compound', 'second-compound'
    }
