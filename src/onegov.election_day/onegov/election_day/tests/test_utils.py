from datetime import date, datetime
from freezegun import freeze_time
from mock import Mock
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.ballot import ComplexVote
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from onegov.election_day.tests import DummyRequest
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import add_local_results
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_election_summary
from onegov.election_day.utils import get_summaries
from onegov.election_day.utils import get_summary
from onegov.election_day.utils import get_vote_summary
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


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


def test_add_local_results_simple(session):
    target = ArchivedResult()

    be = Canton(name='BE', canton='be')
    bern = Municipality(name='Bern', municipality='351')

    # wrong principal domain
    add_local_results(ArchivedResult(), target, be, session)
    assert not target.local

    # wrong type
    add_local_results(ArchivedResult(type='election'), target, bern, session)
    assert not target.local

    # missing ID
    add_local_results(ArchivedResult(type='vote'), target, bern, session)
    assert not target.local

    # no vote
    source = ArchivedResult(type='vote', external_id='id')
    add_local_results(source, target, bern, session)
    assert not target.local

    # no proposal
    session.add(Vote(title="Vote", domain='federation', date=date(2011, 1, 1)))
    session.flush()
    vote = session.query(Vote).one()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # no results
    vote.ballots.append(Ballot(type="proposal"))
    session.flush()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # not yet counted
    vote.proposal.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=False, yeas=1000, nays=3000, empty=0, invalid=0
        )
    )
    session.flush()
    proposal = session.query(BallotResult).one()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # simple vote
    proposal.counted = True

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert target.local
    assert target.local_answer == 'rejected'
    assert target.local_yeas_percentage == 25.0
    assert target.local_nays_percentage == 75.0

    proposal.yeas = 7000

    add_local_results(source, target, bern, session)
    assert target.local
    assert target.local_answer == 'accepted'
    assert target.local_yeas_percentage == 70.0
    assert target.local_nays_percentage == 30.0


def test_add_local_results_complex(session):
    target = ArchivedResult()

    be = Canton(name='BE', canton='be')
    bern = Municipality(name='Bern', municipality='351')

    # wrong principal domain
    add_local_results(ArchivedResult(), target, be, session)
    assert not target.local

    # wrong type
    add_local_results(ArchivedResult(type='election'), target, bern, session)
    assert not target.local

    # missing ID
    add_local_results(ArchivedResult(type='vote'), target, bern, session)
    assert not target.local

    # no vote
    source = ArchivedResult(type='vote', external_id='id')
    add_local_results(source, target, bern, session)
    assert not target.local

    # no proposal
    session.add(
        ComplexVote(title="Vote", domain='federation', date=date(2011, 1, 1))
    )
    session.flush()
    vote = session.query(ComplexVote).one()

    # no results
    target = ArchivedResult()
    vote.ballots.append(Ballot(type="counter-proposal"))
    vote.ballots.append(Ballot(type="tie-breaker"))
    session.flush()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # not yet counted
    vote.proposal.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=True, yeas=7000, nays=3000, empty=0, invalid=0
        )
    )
    vote.counter_proposal.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=False, yeas=4000, nays=6000, empty=0, invalid=0
        )
    )
    vote.tie_breaker.results.append(
        BallotResult(
            name='Bern', entity_id=351,
            counted=False, yeas=2000, nays=8000, empty=0, invalid=0
        )
    )
    session.flush()
    proposal = vote.proposal.results.one()
    counter = vote.counter_proposal.results.one()
    tie = vote.tie_breaker.results.one()

    source = ArchivedResult(type='vote', external_id=vote.id)
    add_local_results(source, target, bern, session)
    assert not target.local

    # complex vote
    counter.counted = True
    tie.counted = True

    # p: y, c: n, t:p
    add_local_results(source, target, bern, session)
    assert target.local
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
