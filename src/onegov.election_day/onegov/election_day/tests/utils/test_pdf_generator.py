from datetime import date
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import Vote
from onegov.election_day.tests.utils.common import add_election_compound
from onegov.election_day.tests.utils.common import add_majorz_election
from onegov.election_day.tests.utils.common import add_proporz_election
from onegov.election_day.tests.utils.common import add_vote
from onegov.election_day.tests.utils.common import PatchedD3Renderer
from onegov.election_day.utils.pdf_generator import PdfGenerator
from pdfrw import PdfReader
from unittest.mock import MagicMock
from unittest.mock import patch


class PatchedPdfGenerator(PdfGenerator):
    def __init__(self, app):
        super(PatchedPdfGenerator, self).__init__(app)
        self.renderer = PatchedD3Renderer(app)


def test_generate_pdf_election(session, election_day_app):
    generator = PatchedPdfGenerator(election_day_app)

    # Majorz election
    majorz = add_majorz_election(session)
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(majorz, 'election.pdf', locale)
        with election_day_app.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 3

    # Proporz election
    proporz = add_proporz_election(session)
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(proporz, 'election.pdf', locale)
        with election_day_app.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 8

    # Proporz election with deltas
    add_proporz_election(session, year=2011)
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(proporz, 'election.pdf', locale)
        with election_day_app.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 8

    # Proporz election with more than one entitiy
    proporz.status = 'final'
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(proporz, 'election.pdf', locale)
        with election_day_app.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 8

    # Tacit election
    majorz.tacit = True
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(majorz, 'election.pdf', locale)
        with election_day_app.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 1


def test_generate_pdf_election_compound(session, election_day_app):
    generator = PatchedPdfGenerator(election_day_app)

    compound = add_election_compound(session)
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(compound, 'election.pdf', locale)
        with election_day_app.filestorage.open('election.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 4


def test_generate_pdf_vote(session, election_day_app):
    generator = PatchedPdfGenerator(election_day_app)

    # Simple vote
    vote = add_vote(session, 'simple')
    vote.proposal.results.append(BallotResult(
        name='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(vote, 'vote.pdf', locale)
        with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
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
        with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 9


def test_generate_pdf_vote_districts(session, election_day_app_gr):
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


def test_generate_pdf_vote_single(session, election_day_app):
    generator = PatchedPdfGenerator(election_day_app)

    # Simple vote, only one entity
    vote = add_vote(session, 'simple')
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(vote, 'vote.pdf', locale)
        with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 1

    # Complex vote, only one entity
    vote = add_vote(session, 'complex')
    for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
        generator.generate_pdf(vote, 'vote.pdf', locale)
        with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 3


def test_generate_pdf_long_title(session, election_day_app):
    title = """This is a very long title so that it breaks the header line to
    a second line which must also be ellipsed.

    It is really, really, really, really, really, really, really, really,
    really, really, really, really, really, really, really, really, really,
    really, really, really, really, really, really, really, really, really,
    really, really, really, really, really, really, really, really, really,
    really a long title!
    """

    vote = Vote(title=title, domain='federation', date=date(2015, 6, 18))
    vote.ballots.append(Ballot(type='proposal'))
    session.add(vote)
    session.flush()

    vote.proposal.results.append(
        BallotResult(name='x', yeas=0, nays=100, counted=True, entity_id=1)
    )
    session.flush()

    generator = PatchedPdfGenerator(election_day_app)
    generator.generate_pdf(vote, 'vote.pdf', 'de_CH')
    with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
        assert len(PdfReader(f, decompress=False).pages) == 1


def test_sign_pdf(session, election_day_app):
    # No signing
    generator = PdfGenerator(election_day_app)

    with patch('onegov.pdf.signature.post') as post:
        generator.sign_pdf('vote.pdf')
        assert not post.called

    # signing
    principal = election_day_app.principal
    principal.pdf_signing = {
        'host': 'http://abcd.ef',
        'login': 'abcd',
        'password': '1234',
        'reason': 'why'
    }
    election_day_app.cache.set('principal', principal)
    generator = PdfGenerator(election_day_app)

    with election_day_app.filestorage.open('vote.pdf', 'w') as f:
        f.write('PDF')

    args = {
        'json.return_value': {
            'result': {'signed_data': 'U0lHTkVE'}
        }
    }
    with patch('onegov.pdf.signature.post',
               return_value=MagicMock(**args)) as post:
        generator.sign_pdf('vote.pdf')
        assert post.called
        assert post.call_args[0][0] == (
            'http://abcd.ef/admin_interface/pdf_signature_jobs.json'
        )
        assert post.call_args[1]['headers']['X-LEXWORK-LOGIN'] == 'abcd'
        assert post.call_args[1]['headers']['X-LEXWORK-PASSWORD'] == '1234'
        assert post.call_args[1]['json'] == {
            'pdf_signature_job': {
                'file_name': 'vote.pdf',
                'data': 'UERG',
                'reason_for_signature': 'why'
            }
        }
    with election_day_app.filestorage.open('vote.pdf', 'r') as f:
        assert f.read() == 'SIGNED'


def test_create_pdfs(election_day_app):
    generator = PatchedPdfGenerator(election_day_app)
    session = election_day_app.session()
    fs = election_day_app.filestorage

    generator.create_pdfs()
    assert election_day_app.filestorage.listdir('pdf') == []

    majorz_election = add_majorz_election(session)
    proporz_election = add_proporz_election(session)
    vote = add_vote(session, 'complex')

    generator.create_pdfs()
    assert len(fs.listdir('pdf')) == 12

    generator.create_pdfs()
    assert len(fs.listdir('pdf')) == 12

    fs.touch('pdf/somefile')
    fs.touch('pdf/some.file')
    fs.touch('pdf/.somefile')

    generator.create_pdfs()
    assert len(fs.listdir('pdf')) == 12

    session.delete(vote)
    session.delete(proporz_election)
    session.flush()

    generator.create_pdfs()
    assert len(fs.listdir('pdf')) == 4

    majorz_election.title = 'Election'
    session.flush()

    generator.create_pdfs()
    assert len(fs.listdir('pdf')) == 4

    session.delete(majorz_election)
    session.flush()

    generator.create_pdfs()
    assert len(fs.listdir('pdf')) == 0
