from cgi import FieldStorage
from datetime import date
from io import BytesIO
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.election_day.forms import VoteForm
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from tests.onegov.election_day.common import DummyPostData
from tests.onegov.election_day.common import DummyRequest
from wtforms.validators import InputRequired


def test_vote_form_on_request():
    form = VoteForm()
    form.request = DummyRequest()
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')
    form.on_request()
    assert form.domain.choices == [
        ('federation', 'Federal'),
        ('canton', 'Cantonal'),
        ('municipality', 'Communal'),
    ]
    assert isinstance(form.vote_de.validators[0], InputRequired)
    assert form.vote_fr.validators == []
    assert form.vote_it.validators == []
    assert form.vote_rm.validators == []

    form = VoteForm()
    form.request = DummyRequest()
    form.request.default_locale = 'fr_CH'
    form.request.app.principal = Municipality(
        name='bern', municipality='351', canton='be', canton_name='Kanton Bern'
    )
    form.on_request()
    assert form.domain.choices == [
        ('federation', 'Federal'),
        ('canton', 'Cantonal'),
        ('municipality', 'Communal'),
    ]
    assert form.vote_de.validators == []
    assert isinstance(form.vote_fr.validators[0], InputRequired)
    assert form.vote_it.validators == []
    assert form.vote_rm.validators == []


def test_vote_form_model(election_day_app_zg, related_link_labels,
                         explanations_pdf):
    model = Vote()
    model.id = 'vote'
    model.title_translations = {
        'de_CH': 'Vote (DE)',
        'fr_CH': 'Vote (FR)',
        'it_CH': 'Vote (IT)',
        'rm_CH': 'Vote (RM)',
    }
    model.date = date.today()
    model.domain = 'federation'
    model.shortcode = 'xy'
    model.related_link = 'http://u.rl'
    model.related_link_label = related_link_labels
    model.explanations_pdf = (explanations_pdf, 'explanations.pdf')

    form = VoteForm()
    form.apply_model(model)

    assert form.id.data == 'vote'
    assert form.external_id.data is None
    assert form.vote_de.data == 'Vote (DE)'
    assert form.vote_fr.data == 'Vote (FR)'
    assert form.vote_it.data == 'Vote (IT)'
    assert form.vote_rm.data == 'Vote (RM)'
    assert form.counter_proposal_de.data is None
    assert form.counter_proposal_fr.data is None
    assert form.counter_proposal_it.data is None
    assert form.counter_proposal_rm.data is None
    assert form.tie_breaker_de.data is None
    assert form.tie_breaker_fr.data is None
    assert form.tie_breaker_it.data is None
    assert form.tie_breaker_rm.data is None
    assert form.date.data == date.today()
    assert form.domain.data == 'federation'
    assert form.shortcode.data == 'xy'
    assert form.related_link.data == 'http://u.rl'
    assert form.related_link_label_de.data == 'DE'
    assert form.related_link_label_fr.data == 'FR'
    assert form.related_link_label_it.data == 'IT'
    assert form.related_link_label_rm.data == 'RM'
    assert form.explanations_pdf.data['mimetype'] == 'application/pdf'
    assert form.vote_type.data == 'simple'
    assert form.has_expats.data is False

    fieldsets = [f.label for f in form.fieldsets if f.label]
    assert 'Title of the counter proposal' not in fieldsets
    assert 'Title of the tie breaker' not in fieldsets

    form.id.data = 'a-vote'
    form.external_id.data = '710'
    form.vote_de.data = 'A Vote (DE)'
    form.vote_fr.data = 'A Vote (FR)'
    form.vote_it.data = 'A Vote (IT)'
    form.vote_rm.data = 'A Vote (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.shortcode.data = 'yz'
    form.related_link.data = 'http://ur.l'
    form.explanations_pdf.action = 'delete'
    form.vote_type.data = 'complex'
    form.has_expats.data = True

    form.update_model(model)

    assert model.id == 'a-vote'
    assert model.external_id == '710'
    assert model.title_translations == {
        'de_CH': 'A Vote (DE)',
        'fr_CH': 'A Vote (FR)',
        'it_CH': 'A Vote (IT)',
        'rm_CH': 'A Vote (RM)',
    }
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.shortcode == 'yz'
    assert model.related_link == 'http://ur.l'
    assert model.explanations_pdf is None
    assert model.type == 'simple'
    assert model.has_expats is True

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


def test_vote_form_validate(session):
    model = Vote(
        id='vote',
        title='Vote',
        domain='federation',
        date=date(2015, 6, 14)
    )

    session.add(model)
    session.add(
        Vote(
            id='vote-copy',
            external_id='ext',
            title=model.title,
            domain=model.domain,
            date=model.date
        )
    )
    session.flush()

    form = VoteForm()
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')
    form.on_request()
    form.apply_model(model)
    assert form.id.data == 'vote'
    assert not form.validate()
    assert form.errors == {
        'date': ['This field is required.'],
        'domain': ['This field is required.'],
        'id': ['This field is required.'],
        'vote_de': ['This field is required.'],
        'vote_type': ['This field is required.']
    }

    form = VoteForm(DummyPostData({'id': 'vote copy'}))
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')
    form.on_request()
    form.model = model
    assert not form.validate()
    assert form.errors['id'] == ['Invalid ID']

    form = VoteForm(DummyPostData({
        'id': 'vote-copy',
        'external_id': 'ext',
        'external_id_counter_proposal': 'ext',
        'external_id_tie_breaker': 'ext'
    }))
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')
    form.on_request()
    form.model = model
    assert not form.validate()
    assert form.errors['id'] == ['ID already exists']
    assert form.errors['external_id'] == ['ID already exists']
    assert form.errors['external_id_counter_proposal'] == ['ID already exists']
    assert form.errors['external_id_tie_breaker'] == ['ID already exists']

    form = VoteForm(DummyPostData({
        'external_id': 'e100',
        'external_id_counter_proposal':
        'e100', 'external_id_tie_breaker': 'e100'
    }))
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')
    form.on_request()
    form.model = model
    assert not form.validate()
    assert form.errors['external_id_counter_proposal'] == ['ID already exists']
    assert form.errors['external_id_tie_breaker'] == ['ID already exists']

    form = VoteForm(DummyPostData({
        'date': '2020-01-01',
        'domain': 'federation',
        'id': 'vote-new',
        'external_id': 'external',
        'vote_de': 'Vote',
        'vote_type': 'simple'
    }))
    form.request = DummyRequest(session=session)
    form.request.default_locale = 'de_CH'
    form.request.app.principal = Canton(name='be', canton='be')
    form.on_request()
    form.model = model
    assert form.validate()
    form.update_model(model)
    session.flush()
    assert session.query(Vote).filter_by(id='vote-new').one()


def test_vote_form_model_complex(election_day_app_zg, related_link_labels,
                                 explanations_pdf):
    model = ComplexVote()
    model.id = 'vote'
    model.title_translations = {
        'de_CH': 'Vote (DE)',
        'fr_CH': 'Vote (FR)',
        'it_CH': 'Vote (IT)',
        'rm_CH': 'Vote (RM)',
    }
    model.counter_proposal.title_translations = {
        'de_CH': 'Counter Proposal (DE)',
        'fr_CH': 'Counter Proposal (FR)',
        'it_CH': 'Counter Proposal (IT)',
        'rm_CH': 'Counter Proposal (RM)',
    }
    model.tie_breaker.title_translations = {
        'de_CH': 'Tie Breaker (DE)',
        'fr_CH': 'Tie Breaker (FR)',
        'it_CH': 'Tie Breaker (IT)',
        'rm_CH': 'Tie Breaker (RM)',
    }
    model.date = date.today()
    model.domain = 'federation'
    model.shortcode = 'xy'
    model.related_link = 'http://u.rl'
    model.related_link_label = related_link_labels
    model.explanations_pdf = (explanations_pdf, 'explanations.pdf')

    form = VoteForm()
    form.apply_model(model)

    assert form.id.data == 'vote'
    assert form.external_id.data is None
    assert form.vote_de.data == 'Vote (DE)'
    assert form.vote_fr.data == 'Vote (FR)'
    assert form.vote_it.data == 'Vote (IT)'
    assert form.vote_rm.data == 'Vote (RM)'
    assert form.counter_proposal_de.data == 'Counter Proposal (DE)'
    assert form.counter_proposal_fr.data == 'Counter Proposal (FR)'
    assert form.counter_proposal_it.data == 'Counter Proposal (IT)'
    assert form.counter_proposal_rm.data == 'Counter Proposal (RM)'
    assert form.tie_breaker_de.data == 'Tie Breaker (DE)'
    assert form.tie_breaker_fr.data == 'Tie Breaker (FR)'
    assert form.tie_breaker_it.data == 'Tie Breaker (IT)'
    assert form.tie_breaker_rm.data == 'Tie Breaker (RM)'
    assert form.date.data == date.today()
    assert form.domain.data == 'federation'
    assert form.shortcode.data == 'xy'
    assert form.related_link.data == 'http://u.rl'
    assert form.related_link_label_de.data == 'DE'
    assert form.related_link_label_fr.data == 'FR'
    assert form.related_link_label_it.data == 'IT'
    assert form.related_link_label_rm.data == 'RM'
    assert form.explanations_pdf.data['mimetype'] == 'application/pdf'
    assert form.vote_type.data == 'complex'

    fieldsets = [f.label for f in form.fieldsets if f.label]
    assert 'Title of the counter proposal' in fieldsets
    assert 'Title of the tie breaker' in fieldsets

    form.id.data = 'a-vote'
    form.external_id.data = '740'
    form.external_id_counter_proposal.data = '741'
    form.external_id_tie_breaker.data = '742'
    form.vote_de.data = 'A Vote (DE)'
    form.vote_fr.data = 'A Vote (FR)'
    form.vote_it.data = 'A Vote (IT)'
    form.vote_rm.data = 'A Vote (RM)'
    form.counter_proposal_de.data = 'The Counter Proposal (DE)'
    form.counter_proposal_fr.data = 'The Counter Proposal (FR)'
    form.counter_proposal_it.data = 'The Counter Proposal (IT)'
    form.counter_proposal_rm.data = 'The Counter Proposal (RM)'
    form.tie_breaker_de.data = 'The Tie Breaker (DE)'
    form.tie_breaker_fr.data = 'The Tie Breaker (FR)'
    form.tie_breaker_it.data = 'The Tie Breaker (IT)'
    form.tie_breaker_rm.data = 'The Tie Breaker (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.shortcode.data = 'yz'
    form.related_link.data = 'http://ur.l'
    form.explanations_pdf.action = 'delete'
    form.vote_type.data = 'complex'

    form.update_model(model)

    assert model.id == 'a-vote'
    assert model.external_id == '740'
    assert model.counter_proposal.external_id == '741'
    assert model.tie_breaker.external_id == '742'

    assert model.title_translations == {
        'de_CH': 'A Vote (DE)',
        'fr_CH': 'A Vote (FR)',
        'it_CH': 'A Vote (IT)',
        'rm_CH': 'A Vote (RM)',
    }
    assert model.counter_proposal.title_translations == {
        'de_CH': 'The Counter Proposal (DE)',
        'fr_CH': 'The Counter Proposal (FR)',
        'it_CH': 'The Counter Proposal (IT)',
        'rm_CH': 'The Counter Proposal (RM)',
    }
    assert model.tie_breaker.title_translations == {
        'de_CH': 'The Tie Breaker (DE)',
        'fr_CH': 'The Tie Breaker (FR)',
        'it_CH': 'The Tie Breaker (IT)',
        'rm_CH': 'The Tie Breaker (RM)',
    }
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.shortcode == 'yz'
    assert model.related_link == 'http://ur.l'
    assert model.explanations_pdf is None
    assert model.type == 'complex'

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
