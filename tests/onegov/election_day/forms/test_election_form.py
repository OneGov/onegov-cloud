from cgi import FieldStorage
from datetime import date
from io import BytesIO
from onegov.ballot import Election
from onegov.election_day.forms import ElectionForm
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest
from wtforms.validators import InputRequired


def test_election_form_on_request(session):
    form = ElectionForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='zg', canton='zg')
    form.on_request()
    assert [x[0] for x in form.domain.choices] == [
        'federation', 'canton', 'none', 'municipality'
    ]
    assert form.region.choices == []
    assert form.district.choices == []
    assert len(form.municipality.choices) == 11
    assert isinstance(form.election_de.validators[0], InputRequired)
    assert form.election_fr.validators == []
    assert form.election_it.validators == []
    assert form.election_rm.validators == []

    form = ElectionForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'fr_CH'
    form.request.app.principal = Canton(name='sg', canton='sg')
    form.on_request()
    assert [x[0] for x in form.domain.choices] == [
        'federation', 'canton', 'district', 'none', 'municipality'
    ]
    assert form.region.choices == []
    assert len(form.district.choices) == 18
    assert len(form.municipality.choices) == 95
    assert form.election_de.validators == []
    assert isinstance(form.election_fr.validators[0], InputRequired)
    assert form.election_it.validators == []
    assert form.election_rm.validators == []

    form = ElectionForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'it_CH'
    form.request.app.principal = Canton(name='gr', canton='gr')
    form.on_request()
    assert [x[0] for x in form.domain.choices] == [
        'federation', 'canton', 'region', 'district', 'none', 'municipality'
    ]
    assert len(form.region.choices) == 39
    assert len(form.district.choices) == 15
    assert len(form.municipality.choices) == 232
    assert form.election_de.validators == []
    assert form.election_fr.validators == []
    assert isinstance(form.election_it.validators[0], InputRequired)
    assert form.election_rm.validators == []

    form = ElectionForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'rm_CH'
    form.request.app.principal = Municipality(name='bern', municipality='351')
    form.on_request()
    assert [x[0] for x in form.domain.choices] == [
        'federation', 'canton', 'municipality'
    ]
    assert form.region.choices == []
    assert form.district.choices == []
    assert form.municipality.choices == [('bern', 'bern')]
    assert form.election_de.validators == []
    assert form.election_fr.validators == []
    assert form.election_it.validators == []
    assert isinstance(form.election_rm.validators[0], InputRequired)


def test_election_form_model(election_day_app_zg, related_link_labels,
                             explanations_pdf):
    session = election_day_app_zg.session()

    model = Election()
    model.title = 'Election (DE)'
    model.title_translations['de_CH'] = 'Election (DE)'
    model.title_translations['fr_CH'] = 'Election (FR)'
    model.title_translations['it_CH'] = 'Election (IT)'
    model.title_translations['rm_CH'] = 'Election (RM)'
    model.date = date.today()
    model.domain = 'region'
    model.domain_segment = 'r1'
    model.domain_supersegment = 's1'
    model.shortcode = 'xy'
    model.type = 'proporz'
    model.majority_type = 'relative'
    model.number_of_mandates = 5
    model.related_link = 'http://u.rl'
    model.related_link_label = related_link_labels
    model.explanations_pdf = (explanations_pdf, 'explanations.pdf')
    model.tacit = False
    model.has_expats = False
    model.voters_counts = False
    model.exact_voters_counts = False
    model.horizontal_party_strengths = False
    model.show_party_strengths = False
    model.show_party_panachage = False
    model.colors = {
        'FDP': '#3a8bc1',
        'CVP': '#ff9100',
    }

    form = ElectionForm()
    form.apply_model(model)
    form.request = DummyRequest(session=session)

    assert form.election_de.data == 'Election (DE)'
    assert form.election_fr.data == 'Election (FR)'
    assert form.election_it.data == 'Election (IT)'
    assert form.election_rm.data == 'Election (RM)'
    assert form.date.data == date.today()
    assert form.domain.data == 'region'
    assert form.region.data == 'r1'
    assert form.shortcode.data == 'xy'
    assert form.election_type.data == 'proporz'
    assert form.mandates.data == 5
    assert form.related_link.data == 'http://u.rl'
    assert form.related_link_label_de.data == 'DE'
    assert form.related_link_label_fr.data == 'FR'
    assert form.related_link_label_it.data == 'IT'
    assert form.related_link_label_rm.data == 'RM'
    assert form.explanations_pdf.data['mimetype'] == 'application/pdf'
    assert form.tacit.data is False
    assert form.has_expats.data is False
    assert form.voters_counts.data is False
    assert form.exact_voters_counts.data is False
    assert form.horizontal_party_strengths.data is False
    assert form.show_party_strengths.data is False
    assert form.show_party_panachage.data is False
    assert form.colors.data == (
        'CVP #ff9100\n'
        'FDP #3a8bc1'
    )

    form.election_de.data = 'An Election (DE)'
    form.election_fr.data = 'An Election (FR)'
    form.election_it.data = 'An Election (IT)'
    form.election_rm.data = 'An Election (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'district'
    form.district.data = 'd1'
    form.shortcode.data = 'yz'
    form.election_type.data = 'majorz'
    form.mandates.data = 2
    form.majority_type.data = 'absolute'
    form.absolute_majority.data = 10000
    form.related_link.data = 'http://ur.l'
    form.explanations_pdf.action = 'delete'
    form.tacit.data = True
    form.has_expats.data = True
    form.voters_counts.data = True
    form.exact_voters_counts.data = True
    form.horizontal_party_strengths.data = True
    form.show_party_strengths.data = True
    form.show_party_panachage.data = True
    form.colors.data = (
        'CVP #ff9100\r\n'
        'SP Juso #dd0e0e\n'
        'FDP   #3a8bc1\n'
        'GLP\t\t#aeca00\n'
    )
    form.update_model(model)

    assert model.title == 'An Election (DE)'
    assert model.title_translations['de_CH'] == 'An Election (DE)'
    assert model.title_translations['fr_CH'] == 'An Election (FR)'
    assert model.title_translations['it_CH'] == 'An Election (IT)'
    assert model.title_translations['rm_CH'] == 'An Election (RM)'
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'district'
    assert model.domain_segment == 'd1'
    assert model.domain_supersegment == ''
    assert model.shortcode == 'yz'
    assert model.type == 'majorz'
    assert model.number_of_mandates == 2
    assert model.majority_type == 'absolute'
    assert model.absolute_majority == 10000
    assert model.related_link == 'http://ur.l'
    assert model.explanations_pdf is None
    assert model.tacit is True
    assert model.has_expats is True
    assert model.voters_counts is True
    assert model.exact_voters_counts is True
    assert model.horizontal_party_strengths is True
    assert model.show_party_strengths is True
    assert model.show_party_panachage is True
    assert model.colors == {
        'CVP': '#ff9100',
        'FDP': '#3a8bc1',
        'GLP': '#aeca00',
        'SP Juso': '#dd0e0e',
    }

    form.domain.data = 'municipality'
    form.municipality.data = 'm1'
    form.update_model(model)
    assert model.domain_segment == 'm1'

    # Update supersegment
    form.request.app.principal = Canton('bl')
    form.domain.data = 'region'
    form.date.data = date(2022, 1, 1)
    form.region.data = 'Reinach'
    form.update_model(model)
    assert model.domain == 'region'
    assert model.domain_segment == 'Reinach'
    assert model.domain_supersegment == 'Region 2'

    form.explanations_pdf.action = 'upload'

    field_storage = FieldStorage()
    field_storage.file = BytesIO('my-file'.encode())
    field_storage.type = 'image/png'  # ignored
    field_storage.filename = 'my-file.pdf'
    form.explanations_pdf.process(
        DummyPostData({'explanations_pdf': field_storage})
    )

    form.update_model(model)

    assert model.explanations_pdf.name == 'explanations_pdf'
    assert model.explanations_pdf.reference.filename == 'my-file.pdf'
    assert model.explanations_pdf.reference.file.read() == b'my-file'


def test_election_form_relations(session):
    session.add(
        Election(
            title="First Election",
            domain='federation',
            date=date(2011, 1, 1),
        )
    )
    session.add(
        Election(
            title="Second Election",
            domain='federation',
            date=date(2011, 1, 2),
        )
    )

    # Add a new election with relations
    election = Election()

    form = ElectionForm()
    form.request = DummyRequest(session=session)
    form.request.app.principal = Canton(name='gr', canton='gr')
    form.on_request()
    assert form.related_elections_historical.choices == [
        ('second-election', '02.01.2011 Second Election'),
        ('first-election', '01.01.2011 First Election'),
    ]
    assert form.related_elections_round.choices == [
        ('second-election', '02.01.2011 Second Election'),
        ('first-election', '01.01.2011 First Election'),
    ]

    form.election_de.data = 'Third Election'
    form.date.data = date(2011, 1, 3)
    form.domain.data = 'federation'
    form.mandates.data = 1
    form.shortcode.data = 'SC'
    form.related_elections_historical.data = ['first-election']
    form.related_elections_round.data = ['first-election', 'second-election']
    form.update_model(election)
    session.add(election)
    session.flush()

    # Change existing relations of an election
    election = session.query(Election).filter_by(id='first-election').one()

    form = ElectionForm()
    form.request = DummyRequest(session=session)
    form.request.app.principal = Canton(name='gr', canton='gr')
    form.on_request()
    assert form.related_elections_historical.choices == [
        ('third-election', '03.01.2011 SC Third Election'),
        ('second-election', '02.01.2011 Second Election'),
        ('first-election', '01.01.2011 First Election'),
    ]
    assert form.related_elections_round.choices == [
        ('third-election', '03.01.2011 SC Third Election'),
        ('second-election', '02.01.2011 Second Election'),
        ('first-election', '01.01.2011 First Election'),
    ]
    form.apply_model(election)
    assert form.related_elections_historical.data == ['third-election']
    assert form.related_elections_round.data == ['third-election']

    form.related_elections_historical.data = ['second-election']
    form.related_elections_round.data = ['second-election', 'third-election']
    form.update_model(election)
    session.add(election)
    session.flush()

    # Check all relations
    election = session.query(Election).filter_by(id='first-election').one()
    form.apply_model(election)
    assert form.related_elections_historical.data == ['second-election']
    assert set(form.related_elections_round.data) == {
        'second-election', 'third-election'
    }

    election = session.query(Election).filter_by(id='second-election').one()
    form.apply_model(election)
    assert form.related_elections_historical.data == ['first-election']
    assert set(form.related_elections_round.data) == {
        'first-election', 'third-election'
    }

    election = session.query(Election).filter_by(id='third-election').one()
    form.apply_model(election)
    assert form.related_elections_historical.data == []
    assert set(form.related_elections_round.data) == {
        'first-election', 'second-election'
    }
