from datetime import date
from freezegun import freeze_time
from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
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
        compound = ElectionCompound(
            title="ElectionCompound",
            domain='canton',
            date=date(2011, 1, 1),
        )
        vote = Vote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.add(compound)
        session.add(vote)
        session.flush()

        ts = 1388577600
        he = '4b9e99d2bd5e48d9a569e5f82175d1d2ed59105f8d82a12dc51b673ff12dc1f2'
        assert pdf_filename(election, 'de') == f'election-{he}.{ts}.de.pdf'
        assert pdf_filename(election, 'rm') == f'election-{he}.{ts}.rm.pdf'

        hc = '2ef359817c8f8a7354e201f891cd7c11a13f4e025aa25239c3ad0cabe58bc49b'
        assert pdf_filename(compound, 'de') == f'election-{hc}.{ts}.de.pdf'
        assert pdf_filename(compound, 'rm') == f'election-{hc}.{ts}.rm.pdf'

        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        assert pdf_filename(vote, 'de') == f'vote-{hv}.{ts}.de.pdf'
        assert pdf_filename(vote, 'rm') == f'vote-{hv}.{ts}.rm.pdf'


def test_svg_filename(session):
    with freeze_time("2014-01-01 12:00"):
        election = Election(
            title="Election",
            domain='federation',
            date=date(2011, 1, 1),
        )
        compound = ElectionCompound(
            title="ElectionCompound",
            domain='canton',
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
        session.add(compound)
        session.add(vote)
        session.flush()

        ts = 1388577600
        he = '4b9e99d2bd5e48d9a569e5f82175d1d2ed59105f8d82a12dc51b673ff12dc1f2'
        assert svg_filename(election, 'chart') == \
            f'election-{he}.{ts}.chart.any.svg'
        assert svg_filename(election, 'chart', 'de') == \
            f'election-{he}.{ts}.chart.de.svg'
        assert svg_filename(election, 'chart', 'rm') == \
            f'election-{he}.{ts}.chart.rm.svg'

        hc = '2ef359817c8f8a7354e201f891cd7c11a13f4e025aa25239c3ad0cabe58bc49b'
        assert svg_filename(compound, 'chart') == \
            f'election-{hc}.{ts}.chart.any.svg'
        assert svg_filename(compound, 'chart', 'de') == \
            f'election-{hc}.{ts}.chart.de.svg'
        assert svg_filename(compound, 'chart', 'rm') == \
            f'election-{hc}.{ts}.chart.rm.svg'

        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        assert svg_filename(vote, 'chart') == \
            f'vote-{hv}.{ts}.chart.any.svg'
        assert svg_filename(vote, 'chart', 'de') == \
            f'vote-{hv}.{ts}.chart.de.svg'
        assert svg_filename(vote, 'chart', 'rm') == \
            f'vote-{hv}.{ts}.chart.rm.svg'

        hb = str(ballot.id)
        assert svg_filename(ballot, 'chart') == \
            f'ballot-{hb}.{ts}.chart.any.svg'
        assert svg_filename(ballot, 'chart', 'de') == \
            f'ballot-{hb}.{ts}.chart.de.svg'
        assert svg_filename(ballot, 'chart', 'rm') == \
            f'ballot-{hb}.{ts}.chart.rm.svg'
