from datetime import date, datetime
from mock import Mock
from io import BytesIO
from onegov.ballot import Election, Vote
from onegov.election_day.formats import load_csv
from onegov.election_day.models import Archive
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_archive_links
from onegov.election_day.utils import get_election_summary
from onegov.election_day.utils import get_summaries
from onegov.election_day.utils import get_summary
from onegov.election_day.utils import get_vote_summary


class DummyRequest(object):

    def link(self, model, name=''):
        return '{}/{}'.format(model.__class__.__name__, name).rstrip('/')


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
    election = Election(
        title="Election",
        domain='federation',
        type='majorz',
        date=date(2011, 1, 1),
    )

    assert get_election_summary(election, DummyRequest()) == {
        'date': '2011-01-01',
        'domain': 'federation',
        'progress': {'counted': 0, 'total': 0},
        'title': {'de_CH': 'Election'},
        'type': 'election',
        'url': 'Election'
    }


def test_get_vote_summary(session):
    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2011, 1, 1),
    )

    assert get_vote_summary(vote, DummyRequest()) == {
        'answer': '',
        'date': '2011-01-01',
        'domain': 'federation',
        'nays_percentage': 100.0,
        'progress': {'counted': 0.0, 'total': 0.0},
        'title': {'de_CH': 'Vote'},
        'type': 'vote',
        'url': 'Vote',
        'yeas_percentage': 0.0
    }


def test_get_summary(session):
    r = DummyRequest()

    election = Election(
        title="Election",
        domain='federation',
        type='majorz',
        date=date(2011, 1, 1),
    )
    assert get_summary(election, r) == get_election_summary(election, r)

    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2011, 1, 1),
    )
    assert get_summary(vote, r) == get_vote_summary(vote, r)


def test_get_summaries(session):
    r = DummyRequest()

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

    assert get_summaries([election, vote], r) == [
        get_election_summary(election, r),
        get_vote_summary(vote, r)
    ]


def test_get_archive_links(session):
    request = DummyRequest()
    archive = Archive(session)

    assert archive.get_years() == []

    for year in (2009, 2011, 2014, 2016):
        session.add(
            Election(
                title="Election {}".format(year),
                domain='federation',
                type='majorz',
                date=date(year, 1, 1),
            )
        )
    for year in (2007, 2011, 2015, 2016):
        session.add(
            Vote(
                title="Vote {}".format(year),
                domain='federation',
                date=date(year, 1, 1),
            )
        )

    session.flush()

    assert set(get_archive_links(archive, request).keys()) == \
        set(['2016', '2015', '2014', '2011', '2009', '2007'])
