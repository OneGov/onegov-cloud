from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.models import Vote
from onegov.election_day.utils import pdf_filename
from onegov.election_day.utils import svg_filename


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_pdf_filename(session: Session) -> None:
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
        assert pdf_filename(compound, 'de') == f'elections-{hc}.{ts}.de.pdf'
        assert pdf_filename(compound, 'rm') == f'elections-{hc}.{ts}.rm.pdf'

        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        assert pdf_filename(vote, 'de') == f'vote-{hv}.{ts}.de.pdf'
        assert pdf_filename(vote, 'rm') == f'vote-{hv}.{ts}.rm.pdf'


def test_svg_filename(session: Session) -> None:
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
        assert vote.proposal  # create
        session.add(election)
        session.add(compound)
        session.add(vote)
        session.flush()
        part = ElectionCompoundPart(compound, 'superregion', 'Region 1')

        ts = 1388577600
        he = '4b9e99d2bd5e48d9a569e5f82175d1d2ed59105f8d82a12dc51b673ff12dc1f2'
        assert svg_filename(election, 'chart', 'de') == (
            f'election-{he}.{ts}.chart.de.svg')
        assert svg_filename(election, 'chart', 'rm') == (
            f'election-{he}.{ts}.chart.rm.svg')

        hc = '2ef359817c8f8a7354e201f891cd7c11a13f4e025aa25239c3ad0cabe58bc49b'
        assert svg_filename(compound, 'chart', 'de') == (
            f'elections-{hc}.{ts}.chart.de.svg')
        assert svg_filename(compound, 'chart', 'rm') == (
            f'elections-{hc}.{ts}.chart.rm.svg')
        assert svg_filename(part, 'chart', 'de') == (
            f'elections-{hc}-region-1.{ts}.chart.de.svg')
        assert svg_filename(part, 'chart', 'rm') == (
            f'elections-{hc}-region-1.{ts}.chart.rm.svg')

        hv = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'
        assert svg_filename(vote, 'chart', 'de') == (
            f'vote-{hv}.{ts}.chart.de.svg')
        assert svg_filename(vote, 'chart', 'rm') == (
            f'vote-{hv}.{ts}.chart.rm.svg')

        hb = str(vote.proposal.id)
        assert svg_filename(vote.proposal, 'chart', 'de') == (
            f'ballot-{hb}.{ts}.chart.de.svg')
        assert svg_filename(vote.proposal, 'chart', 'rm') == (
            f'ballot-{hb}.{ts}.chart.rm.svg')
