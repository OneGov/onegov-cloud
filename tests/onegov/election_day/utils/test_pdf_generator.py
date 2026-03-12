from __future__ import annotations

from datetime import date
from datetime import timedelta
from onegov.election_day.models import BallotResult
from onegov.election_day.models import Vote
from onegov.election_day.utils.pdf_generator import PdfGenerator
from pdfrw import PdfReader  # type: ignore[import-untyped]
from tests.onegov.election_day.common import DummyRequest
from tests.onegov.election_day.utils.common import add_election_compound
from tests.onegov.election_day.utils.common import add_majorz_election
from tests.onegov.election_day.utils.common import add_proporz_election
from tests.onegov.election_day.utils.common import add_vote
from tests.onegov.election_day.utils.common import PatchedD3Renderer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


class PatchedPdfGenerator(PdfGenerator):
    def __init__(self, app: TestApp) -> None:
        renderer = PatchedD3Renderer(app)
        request: Any = DummyRequest(app=app)
        super().__init__(app, request, renderer)


def test_generate_pdf_election(
    session: Session,
    election_day_app_zg: TestApp
) -> None:

    assert election_day_app_zg.filestorage is not None
    generator = PatchedPdfGenerator(election_day_app_zg)

    # Majorz election
    majorz = add_majorz_election(session)
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(majorz, 'election.pdf', locale)
        with election_day_app_zg.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 3

    # Proporz election
    proporz = add_proporz_election(session)
    proporz.show_party_strengths = True
    proporz.show_party_panachage = True
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(proporz, 'election.pdf', locale)
        with election_day_app_zg.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 8

    # Proporz election with deltas
    add_proporz_election(session, year=2011)
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(proporz, 'election.pdf', locale)
        with election_day_app_zg.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 8

    # Proporz election with more than one entitiy
    proporz.status = 'final'
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(proporz, 'election.pdf', locale)
        with election_day_app_zg.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 8

    # Tacit election
    majorz.tacit = True
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(majorz, 'election.pdf', locale)
        with election_day_app_zg.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 1


def test_generate_pdf_election_compound(
    session: Session,
    election_day_app_bl: TestApp
) -> None:

    assert election_day_app_bl.filestorage is not None
    generator = PatchedPdfGenerator(election_day_app_bl)

    election = add_proporz_election(session)
    compound = add_election_compound(session, elections=[election])
    compound.pukelsheim = True
    compound.show_seat_allocation = True
    compound.show_list_groups = True
    compound.show_party_strengths = True
    compound.show_party_panachage = True
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(compound, 'election.pdf', locale)
        with election_day_app_bl.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 8

    # with superregions
    compound.domain_elections = 'region'
    election.domain_supersegment = 'Region 1'
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(compound, 'election.pdf', locale)
        with election_day_app_bl.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 9


def test_generate_pdf_vote(
    session: Session,
    election_day_app_zg: TestApp
) -> None:

    assert election_day_app_zg.filestorage is not None
    generator = PatchedPdfGenerator(election_day_app_zg)

    # Simple vote
    vote = add_vote(session, 'simple')
    vote.proposal.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(vote, 'vote.pdf', locale)
        with election_day_app_zg.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 3

    # Complex vote
    vote = add_vote(session, 'complex')
    vote.proposal.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    vote.counter_proposal.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    vote.tie_breaker.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(vote, 'vote.pdf', locale)
        with election_day_app_zg.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 9


def test_generate_pdf_vote_districts(
    session: Session,
    election_day_app_gr: TestApp
) -> None:

    assert election_day_app_gr.filestorage is not None
    generator = PatchedPdfGenerator(election_day_app_gr)

    # Simple vote
    vote = add_vote(session, 'simple')
    vote.proposal.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(vote, 'vote.pdf', locale)
        with election_day_app_gr.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 5

    # Complex vote
    vote = add_vote(session, 'complex')
    vote.proposal.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    vote.counter_proposal.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    vote.tie_breaker.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(vote, 'vote.pdf', locale)
        with election_day_app_gr.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 15


def test_generate_pdf_long_title(
    session: Session,
    election_day_app_zg: TestApp
) -> None:

    assert election_day_app_zg.filestorage is not None
    title = """This is a very long title so that it breaks the header line to
    a second line which must also be ellipsed.

    It is really, really, really, really, really, really, really, really,
    really, really, really, really, really, really, really, really, really,
    really, really, really, really, really, really, really, really, really,
    really, really, really, really, really, really, really, really, really,
    really a long title!
    """

    vote = Vote(title=title, domain='federation', date=date(2015, 6, 18))
    assert vote.proposal  # create
    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(name='x', yeas=0, nays=100, counted=True, entity_id=1)
    )
    session.flush()

    generator = PatchedPdfGenerator(election_day_app_zg)
    generator.generate_pdf(vote, 'vote.pdf', 'de_CH')
    with election_day_app_zg.filestorage.open('vote.pdf', 'rb') as f:
        assert len(PdfReader(f, decompress=False).pages) == 3


def test_create_pdfs(election_day_app_zg: TestApp) -> None:
    generator = PatchedPdfGenerator(election_day_app_zg)
    session = election_day_app_zg.session()
    fs = election_day_app_zg.filestorage
    assert fs is not None

    generator.create_pdfs()
    assert fs.listdir('pdf') == []

    majorz_election = add_majorz_election(session)
    proporz_election = add_proporz_election(session)
    vote = add_vote(session, 'complex')
    assert majorz_election.last_result_change is None  # used later

    # create
    assert generator.create_pdfs() == (12, 0)
    assert len(fs.listdir('pdf')) == 12

    # don't recreate
    assert generator.create_pdfs() == (0, 0)
    assert len(fs.listdir('pdf')) == 12

    # remove foreign files
    fs.touch('pdf/somefile')
    fs.touch('pdf/some.file')
    fs.touch('pdf/.somefile')

    assert generator.create_pdfs() == (0, 3)
    assert len(fs.listdir('pdf')) == 12

    # remove obsolete files
    session.delete(vote)
    session.delete(proporz_election)
    session.flush()

    assert generator.create_pdfs() == (0, 8)
    assert len(fs.listdir('pdf')) == 4

    # recreate after changes
    majorz_election.title = 'Election'
    session.flush()

    assert generator.create_pdfs() == (4, 4)
    assert len(fs.listdir('pdf')) == 4

    # recreate with new results
    majorz_election.last_result_change = majorz_election.timestamp()
    majorz_election.last_result_change += timedelta(days=1)
    session.flush()

    assert generator.create_pdfs() == (4, 4)
    assert len(fs.listdir('pdf')) == 4

    # recreate when clearing results
    old = fs.listdir('pdf')
    majorz_election.last_result_change = None
    session.flush()

    assert generator.create_pdfs() == (4, 4)
    assert len(fs.listdir('pdf')) == 4
    assert set(old) & set(fs.listdir('pdf')) == set()

    # remove obsolete
    session.delete(majorz_election)
    session.flush()

    assert generator.create_pdfs() == (0, 4)
    assert len(fs.listdir('pdf')) == 0
