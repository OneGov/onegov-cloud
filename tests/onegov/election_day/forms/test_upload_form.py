from __future__ import annotations

import transaction

from datetime import date
from onegov.election_day.forms import UploadElectionCompoundForm
from onegov.election_day.forms import UploadMajorzElectionForm
from onegov.election_day.forms import UploadPartyResultsForm
from onegov.election_day.forms import UploadProporzElectionForm
from onegov.election_day.forms import UploadRestForm
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.models import Canton
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.models import Election
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyPostData


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_upload_vote_form(session: Session) -> None:
    principal = Canton(name='be', canton='be')
    vote = Vote(title='Vote', date=date(2017, 1, 1), domain='canton')

    # Test if wabsti_c is added when data sources are available
    form = UploadVoteForm()
    assert sorted(f[0] for f in form.file_format.choices) == ['internal']

    session.add(vote)
    session.add(DataSource(name='test', type='vote'))
    session.flush()
    ds = session.query(DataSource).one()
    ds.items.append(DataSourceItem(vote_id=ds.query_candidates().one().id))
    transaction.commit()
    vote = session.query(Vote).one()

    form.adjust(principal, vote)
    assert sorted(f[0] for f in form.file_format.choices) == [
        'internal', 'wabsti_c'
    ]

    # Test required fields
    form = UploadVoteForm()
    form.adjust(principal, vote)
    form.process(DummyPostData({'file_format': 'internal'}))
    form.proposal.data = {'mimetype': 'text/plain'}
    assert form.validate()


def test_upload_election_form(session: Session) -> None:
    principal = Canton(name='be', canton='be')
    election = Election(
        title='Election', date=date(2017, 1, 1), domain='canton', type='majorz'
    )

    # Test if wabsti_c is added when data sources are available
    form_majorz = UploadMajorzElectionForm()
    assert sorted(f[0] for f in form_majorz.file_format.choices) == [
        'internal'
    ]
    form_proporz = UploadProporzElectionForm()
    assert sorted(f[0] for f in form_proporz.file_format.choices) == [
        'internal'
    ]

    session.add(election)
    session.add(DataSource(name='test', type='majorz'))
    session.flush()
    ds = session.query(DataSource).one()
    ds.items.append(DataSourceItem(election_id=ds.query_candidates().one().id))
    transaction.commit()
    election = session.query(Election).one()

    form_majorz.adjust(principal, election)
    assert sorted(f[0] for f in form_majorz.file_format.choices) == [
        'internal', 'wabsti_c'
    ]
    form_proporz.adjust(principal, session.query(Election).one())
    assert sorted(f[0] for f in form_proporz.file_format.choices) == [
        'internal', 'wabsti_c'
    ]

    # Test required fields (majorz)
    form = UploadMajorzElectionForm()
    form.adjust(principal, election)
    form.process(DummyPostData({'file_format': 'internal'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    # Test required fields (proporz)
    form2 = UploadProporzElectionForm()
    form2.adjust(principal, election)
    form2.process(DummyPostData({'file_format': 'internal'}))
    form2.results.data = {'mimetype': 'text/plain'}
    assert form2.validate()


def test_upload_party_results_form() -> None:
    form = UploadPartyResultsForm()
    assert not form.validate()

    form = UploadPartyResultsForm(
        DummyPostData({'parties': 'internal'})
    )
    form.parties.data = {'mimetype': 'text/plain'}
    assert form.validate()


def test_upload_rest_form(session: Session) -> None:
    form = UploadRestForm()
    assert not form.validate()

    form = UploadRestForm(DummyPostData({'type': 'vote', 'id': 'vote'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()

    form = UploadRestForm(DummyPostData({'type': 'parties', 'id': 'parties'}))
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()


def test_upload_election_compound_form(session: Session) -> None:
    form = UploadElectionCompoundForm()
    assert not form.validate()

    form = UploadElectionCompoundForm(
        DummyPostData({'file_format': 'internal'})
    )
    form.results.data = {'mimetype': 'text/plain'}
    assert form.validate()
