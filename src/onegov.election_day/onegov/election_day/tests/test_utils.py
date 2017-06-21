from datetime import date, datetime
from freezegun import freeze_time
from mock import Mock
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import Election
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListResult
from onegov.ballot import ListConnection
from onegov.ballot import PanachageResult
from onegov.ballot import PartyResult
from onegov.ballot import Vote
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Principal
from onegov.election_day.tests import DummyRequest
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils import clear_ballot
from onegov.election_day.utils import clear_election
from onegov.election_day.utils import clear_vote
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_election_summary
from onegov.election_day.utils import get_summaries
from onegov.election_day.utils import get_summary
from onegov.election_day.utils import get_vote_summary
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename
from uuid import uuid4


def test_add_last_modified_header():
    response = Mock()

    add_last_modified_header(response, datetime(2011, 12, 31, 12, 1))
    assert str(response.method_calls[0]) \
        == "call.headers.add('Last-Modified', 'Sat, 31 Dec 2011 12:01:00 GMT')"


def test_get_election_summary(session):
    with freeze_time("2014-01-01 12:00"):
        archive = ArchivedResultCollection(session)
        request = DummyRequest()

        election = Election(
            title="Election",
            domain='federation',
            type='majorz',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.flush()

        result = archive.update(election, request)

        expected = {
            'completed': False,
            'date': '2011-01-01',
            'domain': 'federation',
            'elected': [],
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 0, 'total': 0},
            'title': {'de_CH': 'Election'},
            'type': 'election',
            'url': 'Election/election',
        }
        assert expected == get_election_summary(election, request)
        assert expected == get_election_summary(result, None,
                                                request.link(election))


def test_get_vote_summary(session):
    with freeze_time("2014-01-01 12:00"):
        archive = ArchivedResultCollection(session)
        request = DummyRequest()

        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(vote)
        session.flush()

        result = archive.update(vote, request)

        expected = {
            'answer': None,
            'completed': False,
            'date': '2011-01-01',
            'domain': 'federation',
            'last_modified': '2014-01-01T12:00:00+00:00',
            'nays_percentage': None,
            'progress': {'counted': 0.0, 'total': 0.0},
            'title': {'de_CH': 'Vote'},
            'type': 'vote',
            'url': 'Vote/vote',
            'yeas_percentage': None,
        }
        assert expected == get_vote_summary(vote, request)
        assert expected == get_vote_summary(result, None, request.link(vote))

        result.local_answer = 'accepted'
        result.local_yeas_percentage = 60.0
        result.local_nays_percentage = 40.0

        expected['local'] = {
            'answer': 'accepted',
            'nays_percentage': 40.0,
            'yeas_percentage': 60.0,
        }
        assert expected == get_vote_summary(result, None, request.link(vote))


def test_get_summary(session):
    with freeze_time("2014-01-01 12:00"):
        archive = ArchivedResultCollection(session)
        request = DummyRequest()

        election = Election(
            title="Election",
            domain='federation',
            type='majorz',
            date=date(2011, 1, 1),
        )
        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.add(vote)
        session.flush()

        election_result = archive.update(election, request)
        vote_result = archive.update(vote, request)

        assert (
            get_summary(election, request) ==
            get_election_summary(election, request)
        )
        assert (
            get_summary(election_result, request) ==
            get_election_summary(election, request)
        )
        assert (
            get_summary(election_result, request) ==
            get_election_summary(election, None, request.link(election))
        )
        assert (
            get_summary(vote, request) ==
            get_vote_summary(vote, request)
        )
        assert (
            get_summary(vote_result, request) ==
            get_vote_summary(vote, request)
        )
        assert (
            get_summary(vote_result, request) ==
            get_vote_summary(vote, None, request.link(vote))
        )


def test_get_summaries(session):
    with freeze_time("2014-01-01 12:00"):
        archive = ArchivedResultCollection(session)
        request = DummyRequest()

        election = Election(
            title="Election",
            domain='federation',
            type='majorz',
            date=date(2011, 1, 1),
        )
        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.add(vote)
        session.flush()

        election_result = archive.update(election, request)
        vote_result = archive.update(vote, request)

        assert (
            get_summaries(
                [
                    election,
                    election,
                    election_result,
                    election_result,
                    vote,
                    vote,
                    vote_result,
                    vote_result
                ],
                request
            ) == [
                get_election_summary(election, request),
                get_summary(election_result, request),
                get_summary(election_result, request),
                get_election_summary(election, request),
                get_vote_summary(vote, request),
                get_summary(vote_result, request),
                get_summary(vote_result, request),
                get_vote_summary(vote, request)
            ]
        )


def test_get_archive_links(session):
    request = DummyRequest()
    archive = ArchivedResultCollection(session)

    assert archive.get_years() == []

    for year in (2009, 2011, 2014, 2016):
        archive.add(
            Election(
                title="Election {}".format(year),
                domain='federation',
                type='majorz',
                date=date(year, 1, 1),
            ),
            request
        )
    for year in (2007, 2011, 2015, 2016):
        archive.add(
            Vote(
                title="Vote {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            ),
            request
        )

    session.flush()

    assert set(get_archive_links(archive, request).keys()) == \
        set(['2016', '2015', '2014', '2011', '2009', '2007'])


def test_add_local_results(session):
    target = ArchivedResult(meta={})

    be = Principal(name='BE', canton='be')
    bern = Principal(name='Bern', municipality='351')

    # wrong principal domain
    add_local_results(ArchivedResult(), target, be, session)
    assert 'local' not in target.meta

    # wrong type
    add_local_results(ArchivedResult(type='election'), target, bern, session)
    assert 'local' not in target.meta

    # missing ID
    add_local_results(ArchivedResult(type='vote'), target, bern, session)
    assert 'local' not in target.meta

    # no vote
    source = ArchivedResult(type='vote', meta={'id': 'id'})
    add_local_results(source, target, bern, session)
    assert 'local' not in target.meta

    # no proposal
    session.add(Vote(title="Vote", domain='federation', date=date(2011, 1, 1)))
    session.flush()
    vote = session.query(Vote).one()

    source = ArchivedResult(type='vote', meta={'id': vote.id})
    add_local_results(source, target, bern, session)
    assert 'local' not in target.meta

    # no results
    vote.ballots.append(Ballot(type="proposal"))
    session.flush()

    source = ArchivedResult(type='vote', meta={'id': vote.id})
    add_local_results(source, target, bern, session)
    assert 'local' not in target.meta

    # not yet counted
    vote.proposal.results.append(
        BallotResult(
            group='Bern', entity_id=351,
            counted=False, yeas=1000, nays=3000, empty=0, invalid=0
        )
    )
    session.flush()
    proposal = session.query(BallotResult).one()

    source = ArchivedResult(type='vote', meta={'id': vote.id})
    add_local_results(source, target, bern, session)
    assert 'local' not in target.meta

    # simple vote
    proposal.counted = True

    source = ArchivedResult(type='vote', meta={'id': vote.id})
    add_local_results(source, target, bern, session)
    assert 'local' in target.meta
    assert target.local_answer == 'rejected'
    assert target.local_yeas_percentage == 25.0
    assert target.local_nays_percentage == 75.0

    proposal.yeas = 7000

    add_local_results(source, target, bern, session)
    assert 'local' in target.meta
    assert target.local_answer == 'accepted'
    assert target.local_yeas_percentage == 70.0
    assert target.local_nays_percentage == 30.0

    # complex vote
    # no results
    target = ArchivedResult(meta={})
    vote.ballots.append(Ballot(type="counter-proposal"))
    vote.ballots.append(Ballot(type="tie-breaker"))
    session.flush()

    source = ArchivedResult(type='vote', meta={'id': vote.id})
    add_local_results(source, target, bern, session)
    assert 'local' not in target.meta

    # not yet counted
    vote.counter_proposal.results.append(
        BallotResult(
            group='Bern', entity_id=351,
            counted=False, yeas=4000, nays=6000, empty=0, invalid=0
        )
    )
    vote.tie_breaker.results.append(
        BallotResult(
            group='Bern', entity_id=351,
            counted=False, yeas=2000, nays=8000, empty=0, invalid=0
        )
    )
    session.flush()
    counter = vote.counter_proposal.results.one()
    tie = vote.tie_breaker.results.one()

    source = ArchivedResult(type='vote', meta={'id': vote.id})
    add_local_results(source, target, bern, session)
    assert 'local' not in target.meta

    # complex vote
    counter.counted = True
    tie.counted = True

    # p: y, c: n, t:p
    add_local_results(source, target, bern, session)
    assert 'local' in target.meta
    assert target.local_answer == 'proposal'
    assert target.local_yeas_percentage == 70.0
    assert target.local_nays_percentage == 30.0

    # p: y, c: y, t:c
    counter.yeas = 9000
    counter.nays = 1000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'counter-proposal'
    assert target.local_yeas_percentage == 90.0
    assert target.local_nays_percentage == 10.0

    # p: y, c: y, t:p
    tie.yeas = 8000
    tie.nays = 2000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'proposal'
    assert target.local_yeas_percentage == 70.0
    assert target.local_nays_percentage == 30.0

    # p: n, c: y, t:p
    proposal.yeas = 3000
    proposal.nays = 7000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'counter-proposal'
    assert target.local_yeas_percentage == 90.0
    assert target.local_nays_percentage == 10.0

    # p: n, c: n, t:p
    counter.yeas = 1000
    counter.nays = 9000

    add_local_results(source, target, bern, session)
    assert target.local_answer == 'rejected'
    assert target.local_yeas_percentage == 30.0
    assert target.local_nays_percentage == 70.0


def test_pdf_filename(session):
    with freeze_time("2014-01-01 12:00"):
        election = Election(
            title="Election",
            domain='federation',
            type='majorz',
            date=date(2011, 1, 1),
        )
        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.add(vote)
        session.flush()

        he = '4b9e99d2bd5e48d9a569e5f82175d1d2ed59105f8d82a12dc51b673ff12dc1f2'
        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        template = '{name}-{hash}.1388577600.{locale}.pdf'
        assert pdf_filename(election, 'de') == template.format(
            name='election', hash=he, locale='de'
        )
        assert pdf_filename(election, 'rm') == template.format(
            name='election', hash=he, locale='rm'
        )
        assert pdf_filename(vote, 'de') == template.format(
            name='vote', hash=hv, locale='de'
        )
        assert pdf_filename(vote, 'rm') == template.format(
            name='vote', hash=hv, locale='rm'
        )


def test_svg_filename(session):
    with freeze_time("2014-01-01 12:00"):
        election = Election(
            title="Election",
            domain='federation',
            type='majorz',
            date=date(2011, 1, 1),
        )
        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        ballot = Ballot(type="proposal")
        vote.ballots.append(ballot)
        session.add(election)
        session.add(vote)
        session.flush()

        he = '4b9e99d2bd5e48d9a569e5f82175d1d2ed59105f8d82a12dc51b673ff12dc1f2'
        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        template = '{name}-{hash}.1388577600.chart.{locale}.svg'
        assert svg_filename(election, 'chart') == template.format(
            name='election', hash=he, locale='any'
        )
        assert svg_filename(election, 'chart', 'de') == template.format(
            name='election', hash=he, locale='de'
        )
        assert svg_filename(election, 'chart', 'rm') == template.format(
            name='election', hash=he, locale='rm'
        )
        assert svg_filename(vote, 'chart') == template.format(
            name='vote', hash=hv, locale='any'
        )
        assert svg_filename(vote, 'chart', 'de') == template.format(
            name='vote', hash=hv, locale='de'
        )
        assert svg_filename(vote, 'chart', 'rm') == template.format(
            name='vote', hash=hv, locale='rm'
        )
        assert svg_filename(ballot, 'chart') == template.format(
            name='ballot', hash=str(ballot.id), locale='any'
        )
        assert svg_filename(ballot, 'chart', 'de') == template.format(
            name='ballot', hash=str(ballot.id), locale='de'
        )
        assert svg_filename(ballot, 'chart', 'rm') == template.format(
            name='ballot', hash=str(ballot.id), locale='rm'
        )


def test_clear_election(session):
    eid = uuid4()
    pid = uuid4()
    cid = uuid4()
    sid = uuid4()
    lid = uuid4()
    election = Election(
        title='Election',
        type='majorz',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim',
        counted_entities=1,
        total_entities=2,
        absolute_majority=10000
    )
    election.list_connections.append(
        ListConnection(id=pid, connection_id='1')
    )
    election.list_connections.append(
        ListConnection(id=sid, connection_id='2', parent_id=pid)
    )
    election.lists.append(
        List(
            id=lid,
            number_of_mandates=0,
            list_id='A',
            name='List',
            connection_id=sid
        )
    )
    election.candidates.append(
        Candidate(
            id=cid,
            candidate_id='0',
            family_name='X',
            first_name='Y',
            elected=False,
            list_id=lid,
        )
    )
    election.results.append(
        ElectionResult(
            id=eid,
            group='group',
            entity_id=1,
            elegible_voters=100,
            received_ballots=2,
            blank_ballots=3,
            invalid_ballots=4,
            blank_votes=5,
            invalid_votes=6
        )
    )
    election.party_results.append(
        PartyResult(
            year=2017,
            number_of_mandates=0,
            votes=0,
            total_votes=100,
            name='A',
        )
    )

    session.add(ListResult(election_result_id=eid, list_id=lid, votes=10))
    session.add(PanachageResult(target_list_id=lid, source_list_id=1, votes=0))
    session.add(
        CandidateResult(election_result_id=eid, candidate_id=cid, votes=0)
    )

    session.add(election)
    session.flush()

    clear_election(election)

    assert election.counted_entities == 0
    assert election.total_entities == 0
    assert election.absolute_majority is None
    assert election.status is None
    assert election.list_connections.all() == []
    assert election.lists.all() == []
    assert election.candidates.all() == []
    assert election.results.all() == []
    assert election.party_results.all() == []


def test_clear_ballot(session):
    vote = Vote(
        title='Vote',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim'
    )
    vote.ballots.append(Ballot(type='proposal'))
    vote.proposal.results.append(
        BallotResult(
            entity_id=1,
            group='group',
            counted=True,
            yeas=1,
            nays=2,
            empty=3,
            invalid=4,
        )
    )
    session.add(vote)
    session.flush()

    clear_ballot(vote.proposal)

    assert vote.proposal.results.first() == None


def test_clear_vote(session):
    vote = Vote(
        title='Vote',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim'
    )
    vote.ballots.append(Ballot(type='proposal'))
    vote.proposal.results.append(
        BallotResult(
            entity_id=1,
            group='group',
            counted=True,
            yeas=1,
            nays=2,
            empty=3,
            invalid=4,
        )
    )
    session.add(vote)
    session.flush()

    clear_vote(vote)

    assert vote.status is None
    assert [ballot for ballot in vote.ballots] == []
