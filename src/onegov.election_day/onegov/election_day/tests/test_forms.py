from datetime import date
from onegov.ballot import Election, Vote
from onegov.election_day.forms import DataSourceForm
from onegov.election_day.forms import DataSourceItemForm
from onegov.election_day.forms import ElectionForm
from onegov.election_day.forms import SubscribeForm
from onegov.election_day.forms import UploadElectionPartyResultsForm
from onegov.election_day.forms import UploadMajorzElectionForm
from onegov.election_day.forms import UploadProporzElectionForm
from onegov.election_day.forms import UploadRestForm
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.forms import VoteForm
from onegov.election_day.forms.upload import UploadElectionBaseForm
from onegov.election_day.forms.validators import ValidPhoneNumber
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.models import Principal
from pytest import raises
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

    with raises(ValidationError):
        validator(None, Field(1234))
    with raises(ValidationError):
        validator(None, Field('1234'))

    with raises(ValidationError):
        validator(None, Field('+417911122333'))
    with raises(ValidationError):
        validator(None, Field('041791112233'))
    with raises(ValidationError):
        validator(None, Field('041791112233'))
    with raises(ValidationError):
        validator(None, Field('00791112233'))


def test_subscribe_form():
    assert SubscribeForm().formatted_phone_number == None
    assert SubscribeForm(phone_number='').formatted_phone_number == None
    assert SubscribeForm(phone_number=123456).formatted_phone_number == None

    for number in ('0791112233', '0041791112233', '+41791112233'):
        assert SubscribeForm(
            phone_number=number
        ).formatted_phone_number == '+41791112233'


def test_vote_form_domains():
    form = VoteForm()
    assert form.domain.choices == None

    form.set_domain(Principal(name='be', canton='be'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal')
    ]

    form.set_domain(Principal(name='bern', municipality='351'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal'),
        ('municipality', 'Communal')
    ]


def test_vote_form_model(election_day_app):
    model = Vote()
    model.title = 'Vote (DE)'
    model.title_translations['de_CH'] = 'Vote (DE)'
    model.title_translations['fr_CH'] = 'Vote (FR)'
    model.title_translations['it_CH'] = 'Vote (IT)'
    model.title_translations['rm_CH'] = 'Vote (RM)'
    model.date = date.today()
    model.domain = 'federation'
    model.shortcode = 'xy'
    model.meta = {
        'related_link': 'http://u.rl',
        'vote_type': 'simple'
    }

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
    assert form.vote_type.data == 'simple'

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

    assert model.title == 'A Vote (DE)'
    assert model.title_translations['de_CH'] == 'A Vote (DE)'
    assert model.title_translations['fr_CH'] == 'A Vote (FR)'
    assert model.title_translations['it_CH'] == 'A Vote (IT)'
    assert model.title_translations['rm_CH'] == 'A Vote (RM)'
    assert model.date == date(2016, 1, 1)
    assert model.domain == 'canton'
    assert model.shortcode == 'yz'
    assert model.meta['related_link'] == 'http://ur.l'
    assert model.meta['vote_type'] == 'complex'


def test_election_form_domains():
    form = ElectionForm()
    assert ElectionForm().domain.choices == None

    form.set_domain(Principal(name='be', canton='be'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal')
    ]

    form.set_domain(Principal(name='bern', municipality='351'))
    assert sorted(form.domain.choices) == [
        ('canton', 'Cantonal'), ('federation', 'Federal'),
        ('municipality', 'Communal')
    ]


def test_election_form_model(election_day_app):
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
    form.absolute_majority.data = 10000
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
    assert model.absolute_majority == 10000
    assert model.meta['related_link'] == 'http://ur.l'


def test_upload_vote_form():
    cantonal_principal = Principal(name='be', canton='be')
    communal_principal = Principal(name='bern', municipality='351')

    simple_vote = Vote()
    simple_vote.meta = {'vote_type': 'simple'}
    complex_vote = Vote()
    complex_vote.meta = {'vote_type': 'complex'}

    # Test limitation of file formats
    form = UploadVoteForm()
    assert sorted(f[0] for f in form.file_format.choices) == []
    form.adjust(cantonal_principal, simple_vote)
    assert sorted(f[0] for f in form.file_format.choices) == [
        'default', 'internal', 'wabsti'
    ]
    form.adjust(communal_principal, simple_vote)
    assert sorted(f[0] for f in form.file_format.choices) == [
        'default', 'internal'
    ]
    # todo: test if wabsti_c is added when data sources are available

    # Test preseting of vote type
    form = UploadVoteForm()
    assert sorted(f[0] for f in form.type.choices) == ['complex', 'simple']
    form.adjust(cantonal_principal, simple_vote)
    assert sorted(f[0] for f in form.type.choices) == ['simple']
    form.adjust(cantonal_principal, complex_vote)
    assert sorted(f[0] for f in form.type.choices) == ['complex']

    # Test required fields
    form = UploadVoteForm()
    form.adjust(cantonal_principal, simple_vote)
    form.process(DummyPostData({
        'file_format': 'default',
        'type': form.type.data
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm()
    form.adjust(cantonal_principal, complex_vote)
    form.process(DummyPostData({
        'file_format': 'default',
        'type': form.type.data
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert not form.validate()
    form.counter_proposal.data = {'mimetype': 'text/plain'}
    form.tie_breaker.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm()
    form.adjust(cantonal_principal, simple_vote)
    form.process(DummyPostData({
        'file_format': 'internal',
        'type': form.type.data
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm()
    form.adjust(cantonal_principal, complex_vote)
    form.process(DummyPostData({
        'file_format': 'internal',
        'type': form.type.data
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm()
    form.adjust(cantonal_principal, simple_vote)
    form.process(DummyPostData({
        'file_format': 'wabsti',
        'type': form.type.data
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert not form.validate()

    form = UploadVoteForm()
    form.adjust(cantonal_principal, simple_vote)
    form.process(DummyPostData({
        'file_format': 'wabsti',
        'type': form.type.data,
        'vote_number': 1,
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadVoteForm()
    form.adjust(cantonal_principal, complex_vote)
    form.process(DummyPostData({
        'file_format': 'wabsti',
        'type': form.type.data,
        'vote_number': 1,
    }))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()


def test_upload_election_form():
    cantonal_principal = Principal(name='be', canton='be')
    communal_principal = Principal(name='bern', municipality='351')

    election = Election()

    # Test limitation of file formats
    form = UploadElectionBaseForm()
    assert sorted(f[0] for f in form.file_format.choices) == []
    form.adjust(cantonal_principal, election)
    assert sorted(f[0] for f in form.file_format.choices) == [
        'internal', 'sesam', 'wabsti'
    ]
    form.adjust(communal_principal, election)
    assert sorted(f[0] for f in form.file_format.choices) == [
        'internal'
    ]
    # todo: test if wabsti_c is added when data sources are available

    # Test required fields (majorz)
    form = UploadMajorzElectionForm()
    form.adjust(cantonal_principal, election)
    form.process(DummyPostData({'file_format': 'internal'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadMajorzElectionForm()
    form.adjust(cantonal_principal, election)
    form.process(DummyPostData({'file_format': 'sesam'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadMajorzElectionForm()
    form.adjust(cantonal_principal, election)
    form.process(DummyPostData({'file_format': 'wabsti'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    # Test required fields (proporz)
    form = UploadProporzElectionForm()
    form.adjust(cantonal_principal, election)
    form.process(DummyPostData({
        'file_format': 'internal'
    }))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadProporzElectionForm()
    form.adjust(cantonal_principal, election)
    form.process(DummyPostData({'file_format': 'sesam'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadProporzElectionForm()
    form.adjust(cantonal_principal, election)
    form.process(DummyPostData({'file_format': 'wabsti'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()


def test_upload_party_results_form():
    form = UploadElectionPartyResultsForm()
    assert not form.validate()

    form = UploadElectionPartyResultsForm(
        DummyPostData({'parties': 'internal'})
    )
    form.parties.data = {'mimetype': 'text/plain'}
    assert form.validate()


def test_data_source_form():
    # Validation
    assert not DataSourceForm().validate()
    assert DataSourceForm(
        DummyPostData({'name': 'name', 'upload_type': 'vote'})
    ).validate()
    assert DataSourceForm(
        DummyPostData({'name': 'name', 'upload_type': 'majorz'})
    ).validate()
    assert DataSourceForm(
        DummyPostData({'name': 'name', 'upload_type': 'proporz'})
    ).validate()

    # Update model/form
    form = DataSourceForm()
    model = DataSource(type='vote', name='ds_vote')

    form.apply_model(model)
    assert form.upload_type.data == 'vote'
    assert form.name.data == 'ds_vote'

    form.upload_type.data = 'majorz'
    form.name.data = 'ds_majorz'
    form.update_model(model)
    assert model.type == 'majorz'
    assert model.name == 'ds_majorz'


def test_data_source_item_form():
    # Validation
    assert not DataSourceItemForm().validate()
    form = DataSourceItemForm(
        DummyPostData({'district': '1', 'number': '2', 'item': 'item'})
    )
    form.item.choices = [('item', 'Item')]
    assert form.validate()

    # Update model/form
    model = DataSourceItem(
        district='1', number='2', vote_id='vote-id', election_id='election-id'
    )

    form = DataSourceItemForm()
    form.type = 'vote'
    form.apply_model(model)
    assert form.district.data == '1'
    assert form.number.data == '2'
    assert form.item.data == 'vote-id'
    form.district.data = '11'
    form.number.data = '22'
    form.item.data = 'new-vote-id'
    form.update_model(model)
    assert model.district == '11'
    assert model.number == '22'
    assert model.vote_id == 'new-vote-id'

    form = DataSourceItemForm()
    form.type = 'majorz'
    form.apply_model(model)
    assert form.district.data == '11'
    assert form.number.data == '22'
    assert form.item.data == 'election-id'
    form.district.data = '111'
    form.number.data = '222'
    form.item.data = 'new-election-id'
    form.update_model(model)
    assert model.district == '111'
    assert model.number == '222'
    assert model.election_id == 'new-election-id'


def test_data_source_item_form_populate(session):
    form = DataSourceItemForm()

    session.add(DataSource(type='vote', name='dsv'))
    session.add(DataSource(type='majorz', name='dsm'))
    session.add(DataSource(type='proporz', name='dsp'))
    session.flush()

    dsv = session.query(DataSource).filter_by(type='vote').one()
    dsm = session.query(DataSource).filter_by(type='majorz').one()
    dsp = session.query(DataSource).filter_by(type='proporz').one()

    form.populate(dsv)
    assert form.callout == 'No votes yet.'
    assert not form.item.choices

    form.populate(dsm)
    assert form.callout == 'No elections yet.'
    assert not form.item.choices

    form.populate(dsp)
    assert form.callout == 'No elections yet.'
    assert not form.item.choices

    dt = date(2015, 6, 14)
    session.add(Vote(title='v', domain='canton', date=dt))
    session.add(Election(title='m', type='majorz', domain='canton', date=dt))
    session.add(Election(title='p', type='proporz', domain='canton', date=dt))

    form.populate(dsv)
    assert not form.callout
    assert form.item.choices == [('v', 'v')]

    form.populate(dsm)
    assert not form.callout
    assert form.item.choices == [('m', 'm')]

    form.populate(dsp)
    assert not form.callout
    assert form.item.choices == [('p', 'p')]


def test_upload_rest_form(session):
    form = UploadRestForm()
    assert not form.validate()

    form = UploadRestForm(DummyPostData({'type': 'vote', 'id': 'vote'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadRestForm(DummyPostData({'type': 'parties', 'id': 'parties'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()
