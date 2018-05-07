from datetime import date
from freezegun import freeze_time
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.tests.common import DummyRequest
from onegov.election_day.utils import get_election_summary
from onegov.election_day.utils import get_election_compound_summary
from onegov.election_day.utils import get_summaries
from onegov.election_day.utils import get_summary
from onegov.election_day.utils import get_vote_summary


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


def test_get_election_compound_summary(session):
    with freeze_time("2014-01-01 12:00"):
        archive = ArchivedResultCollection(session)
        request = DummyRequest()

        e1 = Election(
            title="e1",
            domain='region',
            date=date(2011, 1, 1),
        )
        e2 = Election(
            title="e2",
            domain='region',
            date=date(2011, 1, 1),
        )
        session.add(e1)
        session.add(e2)
        session.flush()
        compound = ElectionCompound(
            title="Elections",
            domain='canton',
            date=date(2011, 1, 1),
        )

        compound.elections = [e1, e2]
        session.add(compound)
        session.flush()

        result = archive.update(compound, request)

        expected = {
            'completed': False,
            'date': '2011-01-01',
            'domain': 'canton',
            'elections': ['Election/e1', 'Election/e2'],
            'last_modified': '2014-01-01T12:00:00+00:00',
            'progress': {'counted': 0, 'total': 2},
            'title': {'de_CH': 'Elections'},
            'type': 'election_compound',
            'url': 'ElectionCompound/elections',
        }
        assert expected == get_election_compound_summary(compound, request)
        assert expected == get_election_compound_summary(
            result, None, request.link(compound)
        )


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
        election_compound = ElectionCompound(
            title="Elections",
            domain='canton',
            date=date(2011, 1, 1),
        )
        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.add(election_compound)
        session.add(vote)
        session.flush()

        election_compound.elections = [election]

        election_result = archive.update(election, request)
        election_compound_result = archive.update(election_compound, request)
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
            get_summary(election_compound, request) ==
            get_election_compound_summary(election_compound, request)
        )
        assert (
            get_summary(election_compound_result, request) ==
            get_election_compound_summary(election_compound, request)
        )
        assert (
            get_summary(election_compound_result, request) ==
            get_election_compound_summary(
                election_compound, request, request.link(election_compound)
            )
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
        election_compound = ElectionCompound(
            title="Elections",
            domain='canton',
            date=date(2011, 1, 1)
        )
        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(election_compound)
        session.add(election)
        session.add(vote)
        session.flush()

        election_compound.elections = [election]

        election_result = archive.update(election, request)
        election_compound_result = archive.update(election_compound, request)
        vote_result = archive.update(vote, request)

        assert (
            get_summaries(
                [
                    election,
                    election,
                    election_result,
                    election_result,
                    election_compound,
                    election_compound,
                    election_compound_result,
                    election_compound_result,
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
                get_election_compound_summary(election_compound, request),
                get_summary(election_compound_result, request),
                get_summary(election_compound_result, request),
                get_election_compound_summary(election_compound, request),
                get_vote_summary(vote, request),
                get_summary(vote_result, request),
                get_summary(vote_result, request),
                get_vote_summary(vote, request)
            ]
        )
