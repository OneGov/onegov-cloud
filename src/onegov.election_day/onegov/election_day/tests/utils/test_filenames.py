from datetime import date
from freezegun import freeze_time
from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


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
