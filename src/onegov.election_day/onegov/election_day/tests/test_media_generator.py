from base64 import b64encode
from datetime import date
from freezegun import freeze_time
from io import BytesIO, StringIO
from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import Election
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import PanachageResult
from onegov.ballot import PartyResult
from onegov.ballot import Vote
from onegov.election_day import _
from onegov.election_day.utils.media_generator import MediaGenerator
from pdfrw import PdfReader
from pytest import raises
from reportlab.pdfgen.canvas import Canvas
from unittest.mock import patch, MagicMock
from uuid import uuid4


def pdf_chart():
    chart = BytesIO()
    canvas = Canvas(chart, pagesize=(140, 140))
    canvas.drawString(10, 70, "This is a diagram")
    canvas.save()
    return chart


def add_majorz_election(session):
    election = Election(
        title='Majorz Election',
        domain='federation',
        type='majorz',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=200,
        counted_entities=1,
        total_entities=1
    )
    session.add(election)
    session.flush()

    result = ElectionResult(
        group='group',
        entity_id=1,
        elegible_voters=1000,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election.results.append(result)

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        family_name='N1',
        first_name='F1',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        family_name='N2',
        first_name='F2',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_1.id, votes=520)
    )
    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_2.id, votes=111)
    )
    session.flush()

    return election


def add_proporz_election(session, year=2015):
    election = Election(
        title='Proporz Election',
        domain='federation',
        type='proporz',
        date=date(year, 6, 14),
        number_of_mandates=1,
        counted_entities=1,
        total_entities=1
    )
    session.add(election)
    session.flush()

    result = ElectionResult(
        group='group',
        entity_id=1,
        elegible_voters=1000,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election.results.append(result)

    list_1 = List(id=uuid4(), list_id='1', number_of_mandates=1, name='L1')
    list_2 = List(id=uuid4(), list_id='2', number_of_mandates=1, name='L2')
    list_3 = List(id=uuid4(), list_id='3', number_of_mandates=2, name='L3')
    election.lists.append(list_1)
    election.lists.append(list_2)
    election.lists.append(list_3)

    election.party_results.append(
        PartyResult(name='Party 1', number_of_mandates=1, votes=10)
    )
    election.party_results.append(
        PartyResult(name='Party 2', number_of_mandates=1, votes=20)
    )

    list_1.panachage_results.append(
        PanachageResult(target_list_id=list_1.id, source_list_id=2, votes=1)
    )
    list_1.panachage_results.append(
        PanachageResult(target_list_id=list_1.id, source_list_id=3, votes=1)
    )
    list_2.panachage_results.append(
        PanachageResult(target_list_id=list_2.id, source_list_id=1, votes=2)
    )
    list_2.panachage_results.append(
        PanachageResult(target_list_id=list_2.id, source_list_id=3, votes=2)
    )
    list_3.panachage_results.append(
        PanachageResult(target_list_id=list_3.id, source_list_id=1, votes=3)
    )
    list_3.panachage_results.append(
        PanachageResult(target_list_id=list_3.id, source_list_id=2, votes=3)
    )

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        list_id=list_1.id,
        family_name='N1',
        first_name='F1',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        list_id=list_2.id,
        family_name='N2',
        first_name='F2',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_1.id, votes=520)
    )
    result.candidate_results.append(
        CandidateResult(candidate_id=candidate_2.id, votes=111)
    )

    result.list_results.append(ListResult(list_id=list_1.id, votes=520))
    result.list_results.append(ListResult(list_id=list_2.id, votes=111))
    result.list_results.append(ListResult(list_id=list_3.id, votes=21))

    connection_1 = ListConnection(
        id=uuid4(),
        connection_id='A',
        election_id=election.id,
        parent_id=None,
    )
    connection_2 = ListConnection(
        id=uuid4(),
        connection_id='B',
        election_id=election.id,
        parent_id=None,
    )
    subconnection = ListConnection(id=uuid4(), connection_id='B.1')
    connection_2.children.append(subconnection)
    election.list_connections.append(connection_1)
    election.list_connections.append(connection_2)
    election.list_connections.append(subconnection)
    list_1.connection_id = connection_1.id
    list_2.connection_id = connection_2.id
    list_3.connection_id = subconnection.id
    session.flush()

    return election


def add_vote(session, type_):
    vote = Vote(title='Vote', domain='federation', date=date(2015, 6, 18))
    vote.ballots.append(Ballot(type='proposal'))
    if type_ == 'complex':
        vote.ballots.append(Ballot(type='counter-proposal'))
        vote.ballots.append(Ballot(type='tie-breaker'))
    session.add(vote)
    session.flush()

    vote.proposal.results.append(BallotResult(
        group='x', yeas=0, nays=100, counted=True, entity_id=1
    ))
    if type_ == 'complex':
        vote.counter_proposal.results.append(BallotResult(
            group='x', yeas=90, nays=10, counted=True, entity_id=1
        ))
        vote.tie_breaker.results.append(BallotResult(
            group='x', yeas=0, nays=0, counted=True, entity_id=1
        ))
    session.flush()

    return vote


def test_media_generator_scripts(election_day_app):
    generator = MediaGenerator(election_day_app)
    assert len(generator.scripts)


def test_media_generator_translatation(election_day_app):
    generator = MediaGenerator(election_day_app)

    assert generator.translate(_('Election'), 'de_CH') == 'Wahl'
    assert generator.translate(_('Election'), 'fr_CH') == 'Election'
    assert generator.translate(_('Election'), 'it_CH') == 'Elezione'
    assert generator.translate(_('Election'), 'rm_CH') == 'Elecziun'


def test_get_chart(election_day_app):
    generator = MediaGenerator(election_day_app)

    with patch('onegov.election_day.utils.media_generator.post',
               return_value=MagicMock(text='<svg></svg>')) as post:
        data = {'key': 'value'}
        params = {'p': '1'}

        chart = generator.get_chart('bar', 'svg', data, 1000, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 1
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'barChart'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 1000,
            'data': {'key': 'value'},
            'width': 1000
        }

        chart = generator.get_chart('grouped', 'svg', data, 800, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 2
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'groupedChart'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 800,
            'data': {'key': 'value'},
            'width': 800
        }

        chart = generator.get_chart('sankey', 'svg', data, 600, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 3
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'sankeyChart'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 600,
            'data': {'key': 'value'},
            'width': 600
        }

        chart = generator.get_chart('map', 'svg', data, 400, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 4
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'ballotMap'
        assert post.call_args[1]['json']['params'] == {
            'p': '1',
            'viewport_width': 400,
            'data': {'key': 'value'},
            'width': 400
        }

        chart = generator.get_map('svg', data, 2015, 400, params)
        assert chart.read() == '<svg></svg>'
        assert post.call_count == 5
        assert post.call_args[0] == ('http://localhost:1337/d3/svg',)
        assert post.call_args[1]['json']['main'] == 'ballotMap'
        assert post.call_args[1]['json']['params']['width'] == 400
        assert post.call_args[1]['json']['params']['viewport_width'] == 400
        assert post.call_args[1]['json']['params']['p'] == '1'
        assert post.call_args[1]['json']['params']['data'] == data
        assert post.call_args[1]['json']['params']['mapdata']
        assert post.call_args[1]['json']['params']['canton'] == 'zg'

    with patch('onegov.election_day.utils.media_generator.post',
               return_value=MagicMock(text=b64encode('PDF'.encode()))) as post:
        data = {'key': 'value'}

        generator.get_chart('bar', 'pdf', data).read().decode() == 'PDF'
        generator.get_chart('grouped', 'pdf', data).read().decode() == 'PDF'
        generator.get_chart('sankey', 'pdf', data).read().decode() == 'PDF'
        generator.get_chart('map', 'pdf', data).read().decode() == 'PDF'
        generator.get_map('pdf', data, 2015).read().decode() == 'PDF'
        assert post.call_args[0] == ('http://localhost:1337/d3/pdf',)


def test_generate_pdf_election(session, election_day_app):
    generator = MediaGenerator(election_day_app)

    # Majorz election
    election = add_majorz_election(session)
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
            gc.reset_mock()
            generator.generate_pdf(election, 'election.pdf', locale)

            assert gc.call_count == 1
            with election_day_app.filestorage.open('election.pdf', 'rb') as f:
                assert len(PdfReader(f, decompress=False).pages) == 3

    # Proporz election
    election = add_proporz_election(session)
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
            gc.reset_mock()
            generator.generate_pdf(election, 'election.pdf', locale)

            assert gc.call_count == 5
            with election_day_app.filestorage.open('election.pdf', 'rb') as f:
                assert len(PdfReader(f, decompress=False).pages) == 7

    # Proporz election with deltas
    add_proporz_election(session, year=2011)
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
            gc.reset_mock()
            generator.generate_pdf(election, 'election.pdf', locale)

            assert gc.call_count == 5
            with election_day_app.filestorage.open('election.pdf', 'rb') as f:
                assert len(PdfReader(f, decompress=False).pages) == 7

    # Proporz election with more than one entitiy
    election.counted_entities = 5
    election.total_entities = 5
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
            gc.reset_mock()
            generator.generate_pdf(election, 'election.pdf', locale)

            assert gc.call_count == 5
            with election_day_app.filestorage.open('election.pdf', 'rb') as f:
                assert len(PdfReader(f, decompress=False).pages) == 7


def test_generate_pdf_vote(session, election_day_app):
    generator = MediaGenerator(election_day_app)

    # Simple vote
    vote = add_vote(session, 'simple')
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
            gc.reset_mock()
            generator.generate_pdf(vote, 'vote.pdf', locale)

            assert gc.call_count == 1
            with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
                assert len(PdfReader(f, decompress=False).pages) == 2

    # Simple vote with more than one entity
    vote.proposal.results.append(BallotResult(
        group='y', yeas=200, nays=0, counted=True, entity_id=1
    ))
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
            gc.reset_mock()
            generator.generate_pdf(vote, 'vote.pdf', locale)

            assert gc.call_count == 1
            with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
                assert len(PdfReader(f, decompress=False).pages) == 3

    # Complex vote
    vote = add_vote(session, 'complex')
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        for locale in ('de_CH', 'fr_CH', 'it_CH', 'rm_CH'):
            gc.reset_mock()
            generator.generate_pdf(vote, 'vote.pdf', locale)

            assert gc.call_count == 3
            with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
                assert len(PdfReader(f, decompress=False).pages) == 6


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
        BallotResult(group='x', yeas=0, nays=100, counted=True, entity_id=1)
    )
    session.flush()

    generator = MediaGenerator(election_day_app)
    with patch.object(generator, 'get_chart', return_value=pdf_chart()) as gc:
        generator.generate_pdf(vote, 'vote.pdf', 'de_CH')

        assert gc.call_count == 1
        with election_day_app.filestorage.open('vote.pdf', 'rb') as f:
            assert len(PdfReader(f, decompress=False).pages) == 2


def test_sign_pdf(session, election_day_app):
    # No signing
    generator = MediaGenerator(election_day_app)

    with patch('onegov.election_day.utils.media_generator.post') as post:
        generator.sign_pdf('vote.pdf')
        assert not post.called

    # signing
    election_day_app.principal.pdf_signing = {
        'host': 'http://abcd.ef',
        'login': 'abcd',
        'password': '1234',
        'reason': 'why'
    }
    generator = MediaGenerator(election_day_app)

    with election_day_app.filestorage.open('vote.pdf', 'w') as f:
        f.write('PDF')

    args = {
        'json.return_value': {
            'result': {'signed_data': 'U0lHTkVE'}
        }
    }
    with patch('onegov.election_day.utils.media_generator.post',
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


def test_get_pdf_signing_reasons(session, election_day_app):
    # No signing
    generator = MediaGenerator(election_day_app)

    with patch('onegov.election_day.utils.media_generator.get') as get:
        assert generator.signing_reasons() == []
        assert not get.called

    # signing
    election_day_app.principal.pdf_signing = {
        'host': 'http://abcd.ef',
        'login': 'abcd',
        'password': '1234',
        'reason': 'why'
    }
    generator = MediaGenerator(election_day_app)

    args = {
        'json.return_value': {
            'result': ['a', 'b', 'c']
        }
    }
    with patch('onegov.election_day.utils.media_generator.get',
               return_value=MagicMock(**args)) as get:
        assert generator.signing_reasons() == ['a', 'b', 'c']
        assert get.called
        assert get.call_args[0][0] == (
            'http://abcd.ef/admin_interface/pdf_signature_reasons.json'
        )
        assert get.call_args[1]['headers']['X-LEXWORK-LOGIN'] == 'abcd'
        assert get.call_args[1]['headers']['X-LEXWORK-PASSWORD'] == '1234'


def test_generate_svg(election_day_app, session):

    generator = MediaGenerator(election_day_app)

    with raises(AssertionError):
        generator.generate_svg(None, 'things', 'de_CH')

    chart = StringIO('<svg></svg>')
    with patch.object(generator, 'get_chart', return_value=chart) as gc:

        with freeze_time("2014-04-04 14:00"):
            item = add_majorz_election(session)
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'candidates')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'parties', 'de_CH')
            generator.generate_svg(item, 'panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')

            item = add_proporz_election(session)
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'parties', 'de_CH')
            generator.generate_svg(item, 'panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')

            item = add_vote(session, 'complex').proposal
            generator.generate_svg(item, 'lists', 'de_CH')
            generator.generate_svg(item, 'candidates', 'de_CH')
            generator.generate_svg(item, 'connections', 'de_CH')
            generator.generate_svg(item, 'parties', 'de_CH')
            generator.generate_svg(item, 'panachage', 'de_CH')
            generator.generate_svg(item, 'map', 'de_CH')
            generator.generate_svg(item, 'map', 'it_CH')

        with freeze_time("2015-05-05 15:00"):
            generator.generate_svg(item, 'map', 'it_CH')

        assert gc.call_count == 9  # 2 + 5 + 2 + 0

        ts = '1396620000'
        h1 = '41c18975bf916862ed817b7c569b6f242ca7ad9f86ca73bbabd8d9cb26858440'
        h2 = '624b5f68761f574adadba4145283baf97f21e2bd8b87d054b57d936dac6dedff'
        h3 = item.id
        assert sorted(election_day_app.filestorage.listdir('svg')) == sorted([
            'election-{}.{}.candidates.de_CH.svg'.format(h1, ts),
            'election-{}.{}.candidates.any.svg'.format(h1, ts),
            'election-{}.{}.lists.de_CH.svg'.format(h2, ts),
            'election-{}.{}.candidates.de_CH.svg'.format(h2, ts),
            'election-{}.{}.connections.de_CH.svg'.format(h2, ts),
            'election-{}.{}.parties.de_CH.svg'.format(h2, ts),
            'election-{}.{}.panachage.de_CH.svg'.format(h2, ts),
            'ballot-{}.{}.map.de_CH.svg'.format(h3, ts),
            'ballot-{}.{}.map.it_CH.svg'.format(h3, ts)
        ])


def test_create_pdfs(election_day_app):
    generator = MediaGenerator(election_day_app)
    session = election_day_app.session()
    fs = election_day_app.filestorage

    chart = pdf_chart()
    with patch.object(generator, 'get_chart', return_value=chart) as gc:

        generator.create_pdfs()
        assert gc.call_count == 0
        assert election_day_app.filestorage.listdir('pdf') == []

        majorz_election = add_majorz_election(session)
        proporz_election = add_proporz_election(session)
        vote = add_vote(session, 'complex')

        generator.create_pdfs()
        assert gc.call_count == 36
        assert len(fs.listdir('pdf')) == 12

        generator.create_pdfs()
        assert gc.call_count == 36
        assert len(fs.listdir('pdf')) == 12

        fs.touch('pdf/somefile')
        fs.touch('pdf/some.file')
        fs.touch('pdf/.somefile')

        generator.create_pdfs()
        assert gc.call_count == 36
        assert len(fs.listdir('pdf')) == 12

        session.delete(vote)
        session.delete(proporz_election)
        session.flush()

        generator.create_pdfs()
        assert gc.call_count == 36
        assert len(fs.listdir('pdf')) == 4

        majorz_election.title = 'Election'
        session.flush()

        generator.create_pdfs()
        assert gc.call_count == 40
        assert len(fs.listdir('pdf')) == 4

        session.delete(majorz_election)
        session.flush()

        generator.create_pdfs()
        assert gc.call_count == 40
        assert len(fs.listdir('pdf')) == 0


def test_create_svgs(election_day_app):
    generator = MediaGenerator(election_day_app)
    session = election_day_app.session()
    fs = election_day_app.filestorage

    chart = StringIO('<svg></svg>')
    with patch.object(generator, 'get_chart', return_value=chart) as gc:

        generator.create_svgs()
        assert gc.call_count == 0
        assert election_day_app.filestorage.listdir('svg') == []

        majorz_election = add_majorz_election(session)
        proporz_election = add_proporz_election(session)
        vote = add_vote(session, 'complex')

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 18

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 18

        fs.touch('svg/somefile')
        fs.touch('svg/some.file')
        fs.touch('svg/.somefile')

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 18

        session.delete(vote)
        session.delete(proporz_election)
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 18
        assert len(fs.listdir('svg')) == 1

        majorz_election.title = 'Election'
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 19
        assert len(fs.listdir('svg')) == 1

        session.delete(majorz_election)
        session.flush()

        generator.create_svgs()
        assert gc.call_count == 19
        assert len(fs.listdir('svg')) == 0
