from datetime import date, datetime
from freezegun import freeze_time
from io import BytesIO
from mock import Mock
from onegov.ballot import Election, Vote
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import load_csv
from onegov.election_day.tests import DummyRequest
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_election_summary
from onegov.election_day.utils import get_summaries
from onegov.election_day.utils import get_summary
from onegov.election_day.utils import get_vote_summary


def test_load_csv():
    result = load_csv(BytesIO(), 'text/plain', [])
    assert result[1].error == 'The csv/xls/xlsx file is empty.'

    result = load_csv(BytesIO(''.encode('utf-8')), 'text/plain', [])
    assert result[1].error == 'The csv/xls/xlsx file is empty.'

    result = load_csv(BytesIO('a,b,d'.encode('utf-8')), 'text/plain', ['c'])
    assert 'Missing columns' in result[1].error

    result = load_csv(BytesIO('a,a,b'.encode('utf-8')), 'text/plain', ['a'])
    assert result[1].error == 'Some column names appear twice.'

    result = load_csv(BytesIO('<html />'.encode('utf-8')), 'text/plain', ['a'])
    assert result[1].error == 'Not a valid csv/xls/xlsx file.'

    result = load_csv(BytesIO('a,b\n1,2'.encode('utf-8')), 'text/plain', ['a'])
    assert result[1] is None


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
            'date': '2011-01-01',
            'domain': 'federation',
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
            'answer': '',
            'date': '2011-01-01',
            'domain': 'federation',
            'last_modified': '2014-01-01T12:00:00+00:00',
            'nays_percentage': 100.0,
            'progress': {'counted': 0.0, 'total': 0.0},
            'title': {'de_CH': 'Vote'},
            'type': 'vote',
            'url': 'Vote/vote',
            'yeas_percentage': 0.0,
        }
        assert expected == get_vote_summary(vote, request)
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
