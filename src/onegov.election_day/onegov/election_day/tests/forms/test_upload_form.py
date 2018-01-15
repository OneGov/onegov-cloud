import transaction

from datetime import date
from onegov.ballot import ComplexVote
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.election_day.forms import UploadElectionPartyResultsForm
from onegov.election_day.forms import UploadMajorzElectionForm
from onegov.election_day.forms import UploadProporzElectionForm
from onegov.election_day.forms import UploadRestForm
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from onegov.election_day.tests import DummyPostData


def test_upload_vote_form(session):
    cantonal_principal = Canton(name='be', canton='be')
    communal_principal = Municipality(name='bern', municipality='351')

    simple_vote = Vote(title='Vote', date=date(2017, 1, 1), domain='canton')
    complex_vote = ComplexVote()

    # Test limitation of file formats
    form = UploadVoteForm()
    assert sorted(f[0] for f in form.file_format.choices) == []
    form.adjust(cantonal_principal, simple_vote)
    assert sorted(f[0] for f in form.file_format.choices) == [
        'default', 'internal', 'wabsti'
    ]
    form.adjust(communal_principal, simple_vote)
    assert sorted(f[0] for f in form.file_format.choices) == [
        'default', 'internal', 'wabsti_m'
    ]

    # Test if wabsti_c is added when data sources are available
    session.add(simple_vote)
    session.add(DataSource(name='test', type='vote'))
    session.flush()
    ds = session.query(DataSource).one()
    ds.items.append(DataSourceItem(vote_id=ds.query_candidates().one().id))
    transaction.commit()

    form.adjust(cantonal_principal, session.query(Vote).one())
    assert sorted(f[0] for f in form.file_format.choices) == [
        'default', 'internal', 'wabsti', 'wabsti_c'
    ]
    form.adjust(communal_principal, session.query(Vote).one())
    assert sorted(f[0] for f in form.file_format.choices) == [
        'default', 'internal', 'wabsti_c', 'wabsti_m'
    ]

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


def test_upload_election_form(session):
    cantonal_principal = Canton(name='be', canton='be')
    communal_principal = Municipality(name='bern', municipality='351')

    election = Election(
        title='Election', date=date(2017, 1, 1), domain='canton', type='majorz'
    )

    # Test limitation of file formats
    form_majorz = UploadMajorzElectionForm()
    assert sorted(f[0] for f in form_majorz.file_format.choices) == []
    form_majorz.adjust(cantonal_principal, election)
    assert sorted(f[0] for f in form_majorz.file_format.choices) == [
        'internal', 'wabsti'
    ]
    form_majorz.adjust(communal_principal, election)
    assert sorted(f[0] for f in form_majorz.file_format.choices) == [
        'internal', 'wabsti_m'
    ]

    form_proporz = UploadProporzElectionForm()
    assert sorted(f[0] for f in form_proporz.file_format.choices) == []
    form_proporz.adjust(cantonal_principal, election)
    assert sorted(f[0] for f in form_proporz.file_format.choices) == [
        'internal', 'wabsti'
    ]
    form_proporz.adjust(communal_principal, election)
    assert sorted(f[0] for f in form_proporz.file_format.choices) == [
        'internal'
    ]

    # Test if wabsti_c is added when data sources are available
    session.add(election)
    session.add(DataSource(name='test', type='majorz'))
    session.flush()
    ds = session.query(DataSource).one()
    ds.items.append(DataSourceItem(election_id=ds.query_candidates().one().id))
    transaction.commit()

    form_majorz.adjust(cantonal_principal, session.query(Election).one())
    assert sorted(f[0] for f in form_majorz.file_format.choices) == [
        'internal', 'wabsti', 'wabsti_c'
    ]
    form_majorz.adjust(communal_principal, session.query(Election).one())
    assert sorted(f[0] for f in form_majorz.file_format.choices) == [
        'internal', 'wabsti_c', 'wabsti_m'
    ]

    form_proporz.adjust(cantonal_principal, session.query(Election).one())
    assert sorted(f[0] for f in form_proporz.file_format.choices) == [
        'internal', 'wabsti', 'wabsti_c'
    ]
    form_proporz.adjust(communal_principal, session.query(Election).one())
    assert sorted(f[0] for f in form_proporz.file_format.choices) == [
        'internal', 'wabsti_c'
    ]

    # Test required fields (majorz)
    form = UploadMajorzElectionForm()
    form.adjust(cantonal_principal, election)
    form.process(DummyPostData({'file_format': 'internal'}))
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


def test_upload_rest_form(session):
    form = UploadRestForm()
    assert not form.validate()

    form = UploadRestForm(DummyPostData({'type': 'vote', 'id': 'vote'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadRestForm(DummyPostData({'type': 'parties', 'id': 'parties'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()
