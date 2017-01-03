import pytest

from datetime import date
from onegov.ballot import Election, Vote
from onegov.election_day.forms.election import ElectionForm
from onegov.election_day.forms.subscribe import SubscribeForm
from onegov.election_day.forms.upload import UploadElectionForm
from onegov.election_day.forms.upload import UploadVoteForm
from onegov.election_day.forms.validators import ValidPhoneNumber
from onegov.election_day.forms.vote import VoteForm
from wtforms.validators import ValidationError


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_phone_number_validator():

    class Field(object):
        def __init__(self, data):
            self.data = data

    validator = ValidPhoneNumber()

    validator(None, Field(None))
    validator(None, Field(''))

    validator(None, Field('+41791112233'))
    validator(None, Field('0041791112233'))
    validator(None, Field('0791112233'))

    with pytest.raises(ValidationError):
        validator(None, Field(1234))
    with pytest.raises(ValidationError):
        validator(None, Field('1234'))

    with pytest.raises(ValidationError):
        validator(None, Field('+417911122333'))
    with pytest.raises(ValidationError):
        validator(None, Field('041791112233'))
    with pytest.raises(ValidationError):
        validator(None, Field('041791112233'))
    with pytest.raises(ValidationError):
        validator(None, Field('00791112233'))


def test_subscribe_form():
    assert SubscribeForm().formatted_phone_number == None
    assert SubscribeForm(phone_number='').formatted_phone_number == None
    assert SubscribeForm(phone_number=123456).formatted_phone_number == None

    for number in ('0791112233', '0041791112233', '+41791112233'):
        assert SubscribeForm(
            phone_number=number
        ).formatted_phone_number == '+41791112233'


def test_vote_form_choices(election_day_app):
    assert VoteForm().domain.choices == None

    form = VoteForm()
    form.set_domain(election_day_app.principal)
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal')
    ]


def test_vote_form_model(election_day_app):

    election_day_app.session_manager.set_locale(
        default_locale='de_CH', current_locale='de_CH'
    )

    model = Vote()
    model.title = 'Vote (DE)'
    model.title_translations['de_CH'] = 'Vote (DE)'
    model.title_translations['fr_CH'] = 'Vote (FR)'
    model.title_translations['it_CH'] = 'Vote (IT)'
    model.title_translations['rm_CH'] = 'Vote (RM)'
    model.date = date.today()
    model.domain = 'federation'
    model.shortcode = 'xy'
    model.meta = {'related_link': 'http://u.rl'}

    form = VoteForm()
    form.apply_model(model)

    assert form.vote_de.data == 'Vote (DE)'
    assert form.vote_fr.data == 'Vote (FR)'
    assert form.vote_it.data == 'Vote (IT)'
    assert form.vote_rm.data == 'Vote (RM)'
    assert form.date.data == date.today()
    assert form.domain.data == 'federation'
    assert form.shortcode.data == 'xy'
    assert form.related_link.data == 'http://u.rl'

    form.vote_de.data = 'A Vote (DE)'
    form.vote_fr.data = 'A Vote (FR)'
    form.vote_it.data = 'A Vote (IT)'
    form.vote_rm.data = 'A Vote (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.shortcode.data = 'yz'
    form.related_link.data = 'http://ur.l'

    form.update_model(model)

    assert model.title == 'A Vote (DE)'
    assert model.title_translations['de_CH'] == 'A Vote (DE)'
    assert model.title_translations['fr_CH'] == 'A Vote (FR)'
    assert model.title_translations['it_CH'] == 'A Vote (IT)'
    assert model.title_translations['rm_CH'] == 'A Vote (RM)'
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.shortcode == 'yz'
    assert model.meta['related_link'] == 'http://ur.l'


def test_election_form_choices(election_day_app):
    assert ElectionForm().domain.choices == None

    form = ElectionForm()
    form.set_domain(election_day_app.principal)
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal')
    ]


def test_election_form_model(election_day_app):

    election_day_app.session_manager.set_locale(
        default_locale='de_CH', current_locale='de_CH'
    )

    model = Election()
    model.title = 'Election (DE)'
    model.title_translations['de_CH'] = 'Election (DE)'
    model.title_translations['fr_CH'] = 'Election (FR)'
    model.title_translations['it_CH'] = 'Election (IT)'
    model.title_translations['rm_CH'] = 'Election (RM)'
    model.date = date.today()
    model.domain = 'federation'
    model.shortcode = 'xy'
    model.type = 'proporz'
    model.number_of_mandates = 5
    model.meta = {'related_link': 'http://u.rl'}

    form = ElectionForm()
    form.apply_model(model)

    assert form.election_de.data == 'Election (DE)'
    assert form.election_fr.data == 'Election (FR)'
    assert form.election_it.data == 'Election (IT)'
    assert form.election_rm.data == 'Election (RM)'
    assert form.date.data == date.today()
    assert form.domain.data == 'federation'
    assert form.shortcode.data == 'xy'
    assert form.election_type.data == 'proporz'
    assert form.mandates.data == 5
    assert form.related_link.data == 'http://u.rl'

    form.election_de.data = 'An Election (DE)'
    form.election_fr.data = 'An Election (FR)'
    form.election_it.data = 'An Election (IT)'
    form.election_rm.data = 'An Election (RM)'
    form.date.data = date(2016, 1, 1)
    form.domain.data = 'canton'
    form.shortcode.data = 'yz'
    form.election_type.data = 'majorz'
    form.mandates.data = 2
    form.related_link.data = 'http://ur.l'

    form.update_model(model)

    assert model.title == 'An Election (DE)'
    assert model.title_translations['de_CH'] == 'An Election (DE)'
    assert model.title_translations['fr_CH'] == 'An Election (FR)'
    assert model.title_translations['it_CH'] == 'An Election (IT)'
    assert model.title_translations['rm_CH'] == 'An Election (RM)'
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.shortcode == 'yz'
    assert model.type == 'majorz'
    assert model.number_of_mandates == 2
    assert model.meta['related_link'] == 'http://ur.l'


def test_upload_vote_form():
    form = UploadVoteForm(DummyPostData({
        'file_format': 'internal'
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm(DummyPostData({
        'file_format': 'default',
        'type': 'simple'
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm(DummyPostData({
        'file_format': 'default',
        'type': 'complex'
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    form.counter_proposal.data = {'mimetype': 'text/plain'}
    form.tie_breaker.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm(DummyPostData({
        'file_format': 'wabsti',
        'type': 'simple',
        'vote_number': 1
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()


def test_upload_election_form():
    form = UploadElectionForm(DummyPostData({'file_format': 'internal'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadElectionForm(DummyPostData({'file_format': 'sesam'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadElectionForm(DummyPostData({'file_format': 'wabsti'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    def ff(x):
        return 'file_format/{}'.format(x)

    form = UploadElectionForm()
    form.apply_model(Election(type='majorz'))
    assert form.connections.render_kw['data-depends-on'] == ff('none')
    assert form.statistics.render_kw['data-depends-on'] == ff('none')
    assert form.parties.render_kw['data-depends-on'] == ff('none')

    assert form.elected.render_kw['data-depends-on'] == ff('wabsti')
    assert form.complete.render_kw['data-depends-on'] == ff('wabsti')
    assert form.majority.render_kw['data-depends-on'] == ff('!internal')

    form.apply_model(Election(type='proporz'))
    assert form.connections.render_kw['data-depends-on'] == ff('wabsti')
    assert form.statistics.render_kw['data-depends-on'] == ff('wabsti')
    assert 'data-depends-on' not in form.parties.render_kw

    assert form.elected.render_kw['data-depends-on'] == ff('wabsti')
    assert form.complete.render_kw['data-depends-on'] == ff('wabsti')
    assert form.majority.render_kw['data-depends-on'] == ff('none')

    form = UploadElectionForm()
    form.apply_model(Election(type='proporz'))
    assert form.connections.render_kw['data-depends-on'] == ff('wabsti')
    assert form.statistics.render_kw['data-depends-on'] == ff('wabsti')
    assert 'data-depends-on' not in form.parties.render_kw

    assert form.elected.render_kw['data-depends-on'] == ff('wabsti')
    assert form.complete.render_kw['data-depends-on'] == ff('wabsti')
    assert form.majority.render_kw['data-depends-on'] == ff('none')

    form.apply_model(Election(type='majorz'))
    assert form.connections.render_kw['data-depends-on'] == ff('none')
    assert form.statistics.render_kw['data-depends-on'] == ff('none')
    assert form.parties.render_kw['data-depends-on'] == ff('none')

    assert form.elected.render_kw['data-depends-on'] == ff('wabsti')
    assert form.complete.render_kw['data-depends-on'] == ff('wabsti')
    assert form.majority.render_kw['data-depends-on'] == ff('!internal')
