from datetime import date
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.election_day.forms import VoteForm
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from onegov.election_day.tests import DummyRequest
from wtforms.validators import InputRequired


def test_vote_form_domains():
    form = VoteForm()
    assert form.domain.choices is None

    form.set_domain(Canton(name='be', canton='be'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal')
    ]

    form.set_domain(Municipality(name='bern', municipality='351'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal'),
        ('municipality', 'Communal')
    ]


def test_vote_form_translations():
    form = VoteForm()
    form.request = DummyRequest()
    form.request.default_locale = 'de_CH'
    form.on_request()
    assert isinstance(form.vote_de.validators[0], InputRequired)
    assert form.vote_fr.validators == []
    assert form.vote_it.validators == []
    assert form.vote_rm.validators == []

    form = VoteForm()
    form.request = DummyRequest()
    form.request.default_locale = 'fr_CH'
    form.on_request()
    assert form.vote_de.validators == []
    assert isinstance(form.vote_fr.validators[0], InputRequired)
    assert form.vote_it.validators == []
    assert form.vote_rm.validators == []


def test_vote_form_model(election_day_app):
    model = Vote()
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

    form = VoteForm()
    form.apply_model(model)

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
    assert form.vote_type.data == 'simple'

    fieldsets = [f.label for f in form.fieldsets if f.label]
    assert 'Title of the counter proposal' not in fieldsets
    assert 'Title of the tie breaker' not in fieldsets

    form.vote_de.data = 'A Vote (DE)'
    form.vote_fr.data = 'A Vote (FR)'
    form.vote_it.data = 'A Vote (IT)'
    form.vote_rm.data = 'A Vote (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.shortcode.data = 'yz'
    form.related_link.data = 'http://ur.l'
    form.vote_type.data = 'complex'

    form.update_model(model)

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
    assert model.type == 'simple'


def test_vote_form_model_complex(election_day_app):
    model = ComplexVote()
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

    form = VoteForm()
    form.apply_model(model)

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
    assert form.vote_type.data == 'complex'

    fieldsets = [f.label for f in form.fieldsets if f.label]
    assert 'Title of the counter proposal' in fieldsets
    assert 'Title of the tie breaker' in fieldsets

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
    form.vote_type.data = 'complex'

    form.update_model(model)

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
    assert model.type == 'complex'
