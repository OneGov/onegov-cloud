from datetime import date
from datetime import datetime
from decimal import Decimal
from freezegun import freeze_time
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundRelationship
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import ListPanachageResult
from onegov.ballot import PartyPanachageResult
from onegov.ballot import PartyResult
from onegov.ballot import ProporzElection
from onegov.ballot import ElectionCompoundAssociation
from pytz import UTC
from uuid import uuid4


def majorz_election():
    # election
    election = Election(
        title='Majorz',
        id='majorz',
        shortcode='2',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144
    )
    election.title_translations['it_CH'] = 'Elezione'

    # candidates
    candidate_id_1 = uuid4()
    candidate_id_2 = uuid4()
    election.candidates.append(
        Candidate(
            id=candidate_id_1,
            elected=True,
            candidate_id='1',
            family_name='Quimby',
            first_name='Joe',
            party='Republican Party',
            gender='male',
            year_of_birth=1970
        )
    )
    election.candidates.append(
        Candidate(
            id=candidate_id_2,
            elected=False,
            candidate_id='2',
            family_name='Nahasapeemapetilon',
            first_name='Apu',
            party='Democratic Party',
        )
    )

    # results
    election_result = ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=1000,
        expats=35,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120
    )
    election_result.candidate_results.append(
        CandidateResult(candidate_id=candidate_id_1, votes=520)
    )
    election_result.candidate_results.append(
        CandidateResult(candidate_id=candidate_id_2, votes=111)
    )
    election.results.append(election_result)
    return election


def proporz_election(
        title='Proporz',
        id='proporz',
        shortcode='1',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144,
        status=None,
        domain_supersegment=''
):

    # election
    election = ProporzElection(
        title=title,
        id=id,
        shortcode=shortcode,
        domain=domain,
        date=date,
        number_of_mandates=number_of_mandates,
        absolute_majority=absolute_majority,
        status=status,
        domain_supersegment=domain_supersegment
    )
    election.title_translations['it_CH'] = 'Elezione'

    # lists
    list_id_1 = uuid4()
    list_id_2 = uuid4()
    connection = ListConnection(connection_id='A')
    subconnection = ListConnection(id=uuid4(), connection_id='A.1')
    connection.children.append(subconnection)
    election.list_connections.append(connection)
    list_1 = List(
        id=list_id_1,
        list_id='1',
        number_of_mandates=1,
        name='Quimby Again!',
    )
    list_2 = List(
        id=list_id_2,
        list_id='2',
        number_of_mandates=0,
        name='Kwik-E-Major',
        connection_id=subconnection.id
    )
    election.lists.append(list_1)
    election.lists.append(list_2)

    # candidates
    candidate_id_1 = uuid4()
    candidate_id_2 = uuid4()
    election.candidates.append(
        Candidate(
            id=candidate_id_1,
            elected=True,
            candidate_id='1',
            list_id=list_id_1,
            family_name='Quimby',
            first_name='Joe',
            party='Republican Party',
            gender='male',
            year_of_birth=1970
        )
    )
    election.candidates.append(
        Candidate(
            id=candidate_id_2,
            elected=False,
            candidate_id='2',
            list_id=list_id_2,
            family_name='Nahasapeemapetilon',
            first_name='Apu',
            party='Democratic Party',
        )
    )

    # results
    election_result = ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=1000,
        expats=35,
        received_ballots=500,
        blank_ballots=10,
        invalid_ballots=5,
        blank_votes=80,
        invalid_votes=120,
    )

    election_result.candidate_results.append(
        CandidateResult(candidate_id=candidate_id_1, votes=520)
    )
    election_result.candidate_results.append(
        CandidateResult(candidate_id=candidate_id_2, votes=111)
    )

    election_result.list_results.append(
        ListResult(list_id=list_id_1, votes=520)
    )
    election_result.list_results.append(
        ListResult(list_id=list_id_2, votes=111)
    )
    election.results.append(election_result)

    list_1.panachage_results.append(
        ListPanachageResult(source=list_2.list_id, votes=12)
    )
    list_1.panachage_results.append(
        ListPanachageResult(source='99', votes=4)
    )

    return election


def test_election_compound_model(session):
    session.add(
        ElectionCompound(
            title='Legislative Elections',
            domain='canton',
            date=date(2015, 6, 14),
        )
    )
    session.flush()
    election_compound = session.query(ElectionCompound).one()

    assert election_compound.elections == []
    assert election_compound.number_of_mandates == 0
    assert election_compound.allocated_mandates == 0
    assert election_compound.counted is True
    assert election_compound.progress == (0, 0)
    assert election_compound.counted_entities == []
    assert election_compound.has_results is False
    assert election_compound.has_party_results is False
    assert election_compound.has_party_panachage_results is False
    assert election_compound.results == []
    assert election_compound.totals.__dict__ == {
        'turnout': 0,
        'eligible_voters': 0,
        'expats': 0,
        'received_ballots': 0,
        'accounted_ballots': 0,
        'blank_ballots': 0,
        'invalid_ballots': 0,
        'accounted_votes': 0
    }
    assert election_compound.completed is False
    assert election_compound.elected_candidates == []
    assert election_compound.related_link is None
    assert election_compound.last_result_change is None

    # Add two elections
    last_result_change = datetime(2015, 6, 14, 14, 1, tzinfo=UTC)
    session.add(
        Election(
            title="First election",
            domain='region',
            domain_segment='First district',
            date=date(2015, 6, 14),
            number_of_mandates=1,
            last_result_change=last_result_change
        )
    )
    session.add(
        Election(
            title="Second election",
            domain='region',
            domain_segment='Second district',
            date=date(2015, 6, 14),
            number_of_mandates=2,
        )
    )
    session.flush()

    election_compound.elections = session.query(Election).all()
    session.flush()
    assert set([election.id for election in election_compound.elections]) == {
        'first-election', 'second-election'
    }
    assert election_compound.last_result_change == last_result_change

    assert election_compound.number_of_mandates == 3
    assert election_compound.counted is False
    assert election_compound.progress == (0, 2)
    assert election_compound.counted_entities == []
    assert election_compound.allocated_mandates == 0
    assert election_compound.has_results is False
    assert election_compound.has_party_results is False
    assert election_compound.has_party_panachage_results is False
    assert [r.__dict__ for r in election_compound.results] == [
        {
            'accounted_ballots': 0,
            'accounted_votes': 0,
            'blank_ballots': 0,
            'counted': False,
            'domain_segment': 'First district',
            'domain_supersegment': '',
            'eligible_voters': 0,
            'expats': 0,
            'invalid_ballots': 0,
            'received_ballots': 0,
            'turnout': 0
        },
        {
            'accounted_ballots': 0,
            'accounted_votes': 0,
            'blank_ballots': 0,
            'counted': False,
            'domain_segment': 'Second district',
            'domain_supersegment': '',
            'eligible_voters': 0,
            'expats': 0,
            'invalid_ballots': 0,
            'received_ballots': 0,
            'turnout': 0
        }
    ]
    assert sum(election_compound.totals.__dict__.values()) == 0
    assert election_compound.completed is False
    assert election_compound.elected_candidates == []

    # Add results and candidates
    candidates = (('Paul', 'Peter'), ('Max', 'Miro'))
    for index, election in enumerate(election_compound.elections):
        election.results.append(
            ElectionResult(
                name='one',
                entity_id=1,
                counted=False,
                eligible_voters=200,
                expats=20,
                received_ballots=150,
                blank_ballots=6,
                invalid_ballots=15,
                blank_votes=12,
                invalid_votes=9
            )
        )
        election.results.append(
            ElectionResult(
                name='two',
                entity_id=2,
                counted=False,
                eligible_voters=200,
                expats=20,
                received_ballots=150,
                blank_ballots=6,
                invalid_ballots=15,
                blank_votes=12,
                invalid_votes=9
            )
        )
        election.candidates.append(
            Candidate(
                elected=False,
                candidate_id=str(index),
                family_name=candidates[index][0],
                first_name=candidates[index][1],
            )
        )

    assert election_compound.counted is False
    assert election_compound.progress == (0, 2)
    assert election_compound.counted_entities == []
    assert election_compound.allocated_mandates == 0
    assert election_compound.has_results is False
    assert election_compound.has_party_results is False
    assert election_compound.has_party_panachage_results is False
    assert [r.__dict__ for r in election_compound.results] == [
        {
            'accounted_ballots': 258,
            'accounted_votes': 216,
            'blank_ballots': 12,
            'counted': False,
            'domain_segment': 'First district',
            'domain_supersegment': '',
            'eligible_voters': 400,
            'expats': 40,
            'invalid_ballots': 30,
            'received_ballots': 300,
            'turnout': 75.0
        },
        {
            'accounted_ballots': 258,
            'accounted_votes': 474,
            'blank_ballots': 12,
            'counted': False,
            'domain_segment': 'Second district',
            'domain_supersegment': '',
            'eligible_voters': 400,
            'expats': 40,
            'invalid_ballots': 30,
            'received_ballots': 300,
            'turnout': 75.0
        }
    ]
    assert sum(election_compound.totals.__dict__.values()) == 0
    assert election_compound.completed is False

    # Set results as counted
    session.query(ElectionResult).first().counted = True
    assert election_compound.counted is False
    assert election_compound.progress == (0, 2)
    assert election_compound.counted_entities == []
    assert election_compound.allocated_mandates == 0
    assert election_compound.has_results == True
    assert [r.__dict__ for r in election_compound.results] == [
        {
            'accounted_ballots': 258,
            'accounted_votes': 216,
            'blank_ballots': 12,
            'counted': False,
            'domain_segment': 'First district',
            'domain_supersegment': '',
            'eligible_voters': 400,
            'expats': 40,
            'invalid_ballots': 30,
            'received_ballots': 300,
            'turnout': 75.0
        },
        {
            'accounted_ballots': 258,
            'accounted_votes': 474,
            'blank_ballots': 12,
            'counted': False,
            'domain_segment': 'Second district',
            'domain_supersegment': '',
            'eligible_voters': 400,
            'expats': 40,
            'invalid_ballots': 30,
            'received_ballots': 300,
            'turnout': 75.0
        }
    ]
    assert sum(election_compound.totals.__dict__.values()) == 0
    assert election_compound.completed is False

    for result in session.query(ElectionResult):
        result.counted = True
    assert election_compound.counted is True
    assert election_compound.progress == (2, 2)
    assert election_compound.counted_entities == [
        'First district', 'Second district'
    ]
    assert election_compound.allocated_mandates == 0
    assert election_compound.completed == True
    assert election_compound.totals.__dict__ == {
        'accounted_ballots': 258 + 258,
        'accounted_votes': 216 + 474,
        'blank_ballots': 12 + 12,
        'eligible_voters': 400 + 400,
        'expats': 40 + 40,
        'invalid_ballots': 30 + 30,
        'received_ballots': 300 + 300,
        'turnout': 75.0,
    }

    # Set candidates as elected
    session.query(Candidate).filter_by(candidate_id='1').one().elected = True
    assert election_compound.elected_candidates == [('Miro', 'Max')]

    for candidate in session.query(Candidate):
        candidate.elected = True
    assert set(election_compound.elected_candidates) == {
        ('Miro', 'Max'), ('Peter', 'Paul')
    }

    # Add party results
    party_result = PartyResult(
        election_compound_id=election_compound.id,
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name_translations={'en_US': 'Libertarian'},
        party_id='1'
    )
    session.add(party_result)
    session.flush()
    assert election_compound.party_results.one() == party_result
    assert election_compound.has_party_results is False
    party_result.votes = 10
    assert election_compound.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = 10
    assert election_compound.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = 0
    party_result.number_of_mandates = 1
    assert election_compound.has_party_results is True

    # Add panachage results
    panachage_result = PartyPanachageResult(
        election_compound_id=election_compound.id,
        source='A',
        target='B',
        votes=0,
    )
    session.add(panachage_result)
    session.flush()
    assert election_compound.panachage_results.one() == panachage_result
    assert election_compound.has_party_panachage_results is True

    election_compound.last_result_change = election_compound.timestamp()

    # Clear results
    election_compound.clear_results()
    assert election_compound.last_result_change is None
    assert election_compound.party_results.first() is None
    assert election_compound.panachage_results.first() is None
    assert session.query(Candidate).first() is None
    assert session.query(ElectionResult).first() is None

    # Add results again and delete compound
    party_result = PartyResult(
        election_compound_id=election_compound.id,
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name_translations={'en_US': 'Libertarian'},
        party_id='1'
    )
    session.add(party_result)
    session.flush()
    assert election_compound.party_results.one() == party_result

    panachage_result = PartyPanachageResult(
        election_compound_id=election_compound.id,
        source='A',
        target='B',
        votes=0,
    )
    session.add(panachage_result)
    session.flush()
    assert election_compound.panachage_results.one() == panachage_result

    session.delete(election_compound)
    session.flush()

    assert session.query(PartyResult).first() is None
    assert session.query(PartyPanachageResult).first() is None


def test_election_compound_id_generation(session):
    election_compound = ElectionCompound(
        title='Legislative Elections',
        domain='canton',
        date=date(2015, 6, 14),
    )
    session.add(election_compound)
    session.flush()

    assert election_compound.id == 'legislative-elections'

    election = ElectionCompound(
        title='Legislative Elections',
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.id == 'legislative-elections-1'


def test_election_compound_last_modified(session):
    with freeze_time("2001-01-01"):
        compound = ElectionCompound(
            title='Elections',
            domain='canton',
            date=date(2015, 6, 14),
        )
        assert compound.last_modified is None

        session.add(compound)
        session.flush()
        assert compound.last_modified.isoformat().startswith('2001')
        assert session.query(ElectionCompound.last_modified).scalar()\
            .isoformat().startswith('2001')

    with freeze_time("2002-01-01"):
        compound.last_result_change = compound.timestamp()
        session.flush()
        assert compound.last_modified.isoformat().startswith('2002')
        assert session.query(ElectionCompound.last_modified).scalar()\
            .isoformat().startswith('2002')

    with freeze_time("2003-01-01"):
        compound.domain = 'federation'
        session.flush()
        assert compound.last_modified.isoformat().startswith('2003')
        assert session.query(ElectionCompound.last_modified).scalar()\
            .isoformat().startswith('2003')


def test_election_compound_export(session):
    session.add(
        ElectionCompound(
            title='Elections',
            domain='canton',
            date=date(2015, 6, 14),
        )
    )
    election = majorz_election()
    election.colors = {'Democratic Party': '#112233'}
    session.add(election)
    election = proporz_election()
    election.colors = {
        'Democratic Party': '#112233',
        'Kwik-E-Major': '#223344'
    }
    session.add(election)
    session.flush()
    election_compound = session.query(ElectionCompound).one()
    election_compound.title_translations['it_CH'] = 'Elezioni'

    assert election_compound.export(['de_CH']) == []

    election_compound.elections = session.query(Election).filter_by(
        id='majorz'
    ).all()
    session.flush()
    export = election_compound.export(['de_CH', 'fr_CH', 'it_CH'])
    assert export[0] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_date': '2015-06-14',
        'compound_mandates': 1,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'candidate_family_name': 'Nahasapeemapetilon',
        'candidate_first_name': 'Apu',
        'candidate_id': '2',
        'candidate_elected': False,
        'candidate_party': 'Democratic Party',
        'candidate_party_color': '#112233',
        'candidate_gender': '',
        'candidate_year_of_birth': '',
        'candidate_votes': 111
    }
    assert export[1] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_date': '2015-06-14',
        'compound_mandates': 1,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'candidate_family_name': 'Quimby',
        'candidate_first_name': 'Joe',
        'candidate_id': '1',
        'candidate_elected': True,
        'candidate_party': 'Republican Party',
        'candidate_party_color': '',
        'candidate_gender': 'male',
        'candidate_year_of_birth': 1970,
        'candidate_votes': 520
    }

    election_compound.elections = session.query(Election).all()
    session.flush()
    export = election_compound.export(['de_CH', 'fr_CH', 'it_CH'])

    assert export[0] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Proporz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'proporz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'list_name': 'Kwik-E-Major',
        'list_id': '2',
        'list_color': '#223344',
        'list_number_of_mandates': 0,
        'list_votes': 111,
        'list_connection': 'A.1',
        'list_connection_parent': 'A',
        'candidate_family_name': 'Nahasapeemapetilon',
        'candidate_first_name': 'Apu',
        'candidate_id': '2',
        'candidate_elected': False,
        'candidate_party': 'Democratic Party',
        'candidate_party_color': '#112233',
        'candidate_gender': '',
        'candidate_year_of_birth': '',
        'candidate_votes': 111,
        'list_panachage_votes_from_list_1': None,
        'list_panachage_votes_from_list_2': None,
        'list_panachage_votes_from_list_99': None
    }

    assert export[1] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Proporz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'proporz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'list_name': 'Quimby Again!',
        'list_id': '1',
        'list_color': '',
        'list_number_of_mandates': 1,
        'list_votes': 520,
        'list_connection': None,
        'list_connection_parent': None,
        'candidate_family_name': 'Quimby',
        'candidate_first_name': 'Joe',
        'candidate_id': '1',
        'candidate_elected': True,
        'candidate_party': 'Republican Party',
        'candidate_party_color': '',
        'candidate_gender': 'male',
        'candidate_year_of_birth': 1970,
        'candidate_votes': 520,
        'list_panachage_votes_from_list_1': None,
        'list_panachage_votes_from_list_2': 12,
        'list_panachage_votes_from_list_99': 4
    }

    assert export[2] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'candidate_family_name': 'Nahasapeemapetilon',
        'candidate_first_name': 'Apu',
        'candidate_id': '2',
        'candidate_elected': False,
        'candidate_party': 'Democratic Party',
        'candidate_party_color': '#112233',
        'candidate_gender': '',
        'candidate_year_of_birth': '',
        'candidate_votes': 111
    }

    assert export[3] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_superregion': '',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
        'entity_expats': 35,
        'entity_received_ballots': 500,
        'entity_blank_ballots': 10,
        'entity_invalid_ballots': 5,
        'entity_unaccounted_ballots': 15,
        'entity_accounted_ballots': 485,
        'entity_blank_votes': 80,
        'entity_invalid_votes': 120,
        'entity_accounted_votes': 285,
        'candidate_family_name': 'Quimby',
        'candidate_first_name': 'Joe',
        'candidate_id': '1',
        'candidate_elected': True,
        'candidate_party': 'Republican Party',
        'candidate_party_color': '',
        'candidate_gender': 'male',
        'candidate_year_of_birth': 1970,
        'candidate_votes': 520
    }


def test_election_compound_export_parties(session):
    session.add(
        ElectionCompound(
            title='Elections',
            domain='canton',
            date=date(2016, 6, 14),
        )
    )
    session.flush()
    election_compound = session.query(ElectionCompound).one()
    election_compound.colors = {
        'Conservative': 'red',
        'Libertarian': 'black'
    }

    assert election_compound.export_parties(['de_CH'], 'de_CH') == []

    # Add party results
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=0,
            votes=0,
            voters_count=Decimal('1.01'),
            voters_count_percentage=Decimal('100.02'),
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='3',
            year=2012
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=2,
            votes=2,
            voters_count=Decimal('3.01'),
            total_votes=50,
            voters_count_percentage=Decimal('50.02'),
            name_translations={'en_US': 'Libertarian'},
            party_id='3',
            year=2016
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('2.01'),
            total_votes=100,
            voters_count_percentage=Decimal('100.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2012
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='canton',
            number_of_mandates=3,
            votes=3,
            voters_count=Decimal('4.01'),
            total_votes=50,
            voters_count_percentage=Decimal('50.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2016
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='superregion',
            domain_segment='Superregion 1',
            number_of_mandates=1,
            votes=1,
            voters_count=Decimal('1.01'),
            total_votes=10,
            voters_count_percentage=Decimal('10.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2016
        )
    )
    election_compound.party_results.append(
        PartyResult(
            domain='region',
            domain_segment='Region 1',
            number_of_mandates=10,
            votes=10,
            voters_count=Decimal('1.01'),
            total_votes=10,
            voters_count_percentage=Decimal('10.02'),
            name_translations={'en_US': 'Conservative'},
            party_id='5',
            year=2016
        )
    )

    assert election_compound.export_parties(['en_US', 'de_CH'], 'en_US') == [
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '3',
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': 'Libertarian',
            'name_en_US': 'Libertarian',
            'name_de_CH': None,
            'id': '3',
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
        },
        {
            'domain': 'region',
            'domain_segment': 'Region 1',
            'year': 2016,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 10,
            'total_votes': 10,
            'votes': 10,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
        },
        {
            'domain': 'superregion',
            'domain_segment': 'Superregion 1',
            'year': 2016,
            'name': 'Conservative',
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 10,
            'votes': 1,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
        },
    ]

    # Add panachage results
    for idx, source in enumerate(('5', '3', '0', '')):
        election_compound.panachage_results.append(
            PartyPanachageResult(
                target='5',
                source=source,
                votes=idx + 1
            )
        )
    election_compound.panachage_results.append(
        PartyPanachageResult(
            target='3',
            source='5',
            votes=5,
        )
    )
    assert election_compound.export_parties(['de_CH', 'en_US'], 'de_CH') == [
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '3',
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': '3.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_3': None,
            'panachage_votes_from_5': 5,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2016,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '5',
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': '4.01',
            'voters_count_percentage': '50.02',
            'panachage_votes_from_3': 2,
            'panachage_votes_from_5': 1,
            'panachage_votes_from_999': 4,
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Libertarian',
            'id': '3',
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': '1.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_3': None,
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'canton',
            'domain_segment': None,
            'year': 2012,
            'name': None,
            'name_de_CH': None,
            'name_en_US': 'Conservative',
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': '2.01',
            'voters_count_percentage': '100.02',
            'panachage_votes_from_3': None,
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'region',
            'domain_segment': 'Region 1',
            'year': 2016,
            'name': None,
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 10,
            'total_votes': 10,
            'votes': 10,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
        {
            'domain': 'superregion',
            'domain_segment': 'Superregion 1',
            'year': 2016,
            'name': None,
            'name_en_US': 'Conservative',
            'name_de_CH': None,
            'id': '5',
            'color': 'red',
            'mandates': 1,
            'total_votes': 10,
            'votes': 1,
            'voters_count': '1.01',
            'voters_count_percentage': '10.02',
            'panachage_votes_from_5': None,
            'panachage_votes_from_999': None,
        },
    ]


def test_related_election_compounds(session):
    first = ElectionCompound(
        title='First',
        domain='federation',
        date=date(2015, 6, 14)
    )
    second = ElectionCompound(
        title='Second',
        domain='federation',
        date=date(2015, 6, 14)
    )
    session.add(first)
    session.add(second)
    session.flush()
    assert first.related_compounds.all() == []
    assert first.referencing_compounds.all() == []
    assert second.related_compounds.all() == []
    assert second.referencing_compounds.all() == []

    first.related_compounds.append(
        ElectionCompoundRelationship(target_id=second.id)
    )
    session.flush()
    assert first.related_compounds.one().source_id == 'first'
    assert first.related_compounds.one().target_id == 'second'
    assert first.referencing_compounds.all() == []
    assert second.related_compounds.all() == []
    assert second.referencing_compounds.one().source_id == 'first'
    assert second.referencing_compounds.one().target_id == 'second'

    second.related_compounds.append(
        ElectionCompoundRelationship(target_id=first.id)
    )
    session.flush()
    assert first.related_compounds.one().source_id == 'first'
    assert first.related_compounds.one().target_id == 'second'
    assert first.referencing_compounds.one().source_id == 'second'
    assert first.referencing_compounds.one().target_id == 'first'
    assert second.related_compounds.one().source_id == 'second'
    assert second.related_compounds.one().target_id == 'first'
    assert second.referencing_compounds.one().source_id == 'first'
    assert second.referencing_compounds.one().target_id == 'second'

    session.delete(second)
    session.flush()
    assert first.related_compounds.all() == []
    assert first.referencing_compounds.all() == []
    assert session.query(ElectionCompoundRelationship).all() == []

    first.related_compounds.append(
        ElectionCompoundRelationship(target_id=first.id)
    )
    session.flush()
    assert first.related_compounds.one().source_id == 'first'
    assert first.related_compounds.one().target_id == 'first'
    assert first.referencing_compounds.one().source_id == 'first'
    assert first.referencing_compounds.one().target_id == 'first'

    session.delete(first)
    session.flush()
    assert session.query(ElectionCompoundRelationship).all() == []


def test_election_compound_rename(session):
    # Add data
    session.add(majorz_election())
    session.add(proporz_election())
    session.flush()

    election_compound = ElectionCompound(
        title='Elections',
        id='x',
        domain='canton',
        date=date(2015, 6, 14),
    )
    election_compound.elections = session.query(Election).all()
    session.add(election_compound)
    session.flush()
    session.add(
        PartyResult(
            election_compound_id=election_compound.id,
            number_of_mandates=0,
            votes=0,
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='1'
        )
    )
    session.add(
        PartyPanachageResult(
            election_compound_id=election_compound.id,
            source='A',
            target='B',
            votes=0,
        )
    )
    session.flush()

    # Check IDs
    assert session.query(
        ElectionCompoundAssociation.election_compound_id
    ).distinct().scalar() == 'x'
    assert ('x',) in session.query(
        PartyResult.election_compound_id
    ).distinct().all()
    assert ('x',) in session.query(
        PartyPanachageResult.election_compound_id
    ).distinct().all()

    # Change
    election_compound.id = 'y'
    session.flush()

    # Check IDs
    assert session.query(
        ElectionCompoundAssociation.election_compound_id
    ).distinct().scalar() == 'y'
    assert len(election_compound.elections) == 2
    assert ('y',) in session.query(
        PartyResult.election_compound_id
    ).distinct().all()
    assert ('y',) in session.query(
        PartyPanachageResult.election_compound_id
    ).distinct().all()


def test_election_compound_manual_completion(session):

    election_compound = ElectionCompound(
        title='Elections',
        id='elections',
        domain='canton',
        date=date(2020, 3, 22),
    )
    election_1 = proporz_election(
        title='Election 1',
        id='1',
        shortcode='P1',
        domain='region',
        date=date(2020, 3, 22),
        number_of_mandates=1,
        status='interim'
    )
    election_2 = proporz_election(
        title='Election 2',
        id='2',
        shortcode='P2',
        domain='region',
        date=date(2020, 3, 22),
        number_of_mandates=1,
        status='final'
    )
    session.add_all((election_compound, election_1, election_2))
    session.flush()

    # Normal situation
    assert election_compound.completed is False
    assert election_compound.progress == (0, 0)
    assert election_1.completed is False
    assert election_2.completed is True

    election_compound.elections = (election_1, election_2)
    assert election_1.compound == election_compound
    assert election_2.compound == election_compound
    assert election_compound.completed is False
    assert election_compound.progress == (1, 2)
    assert election_1.completed is False
    assert election_2.completed is True

    # Manual completion, not completed
    election_compound.completes_manually = True
    assert election_compound.manually_completed is False
    assert election_compound.completed is False
    assert election_compound.progress == (0, 2)
    assert election_1.completed is False
    assert election_2.completed is False

    election_1.status = 'final'
    assert election_compound.completed is False
    assert election_compound.progress == (0, 2)
    assert election_1.completed is False
    assert election_2.completed is False

    # Manual completion, completed
    election_compound.manually_completed = True
    election_1.status = 'interim'
    assert election_compound.completed is False
    assert election_compound.progress == (1, 2)
    assert election_1.completed is False
    assert election_2.completed is True

    election_1.status = 'final'
    assert election_compound.completed is True
    assert election_compound.progress == (2, 2)
    assert election_1.completed is True
    assert election_2.completed is True


def test_election_compound_supersegment_progress(session):

    election_compound = ElectionCompound(
        title='Elections',
        id='elections',
        domain='canton',
        date=date(2020, 3, 22),
    )
    elections = [
        proporz_election(
            title='Election 1',
            id='1',
            shortcode='P1',
            domain='region',
            date=date(2020, 3, 22),
            number_of_mandates=1,
            status='interim',
            domain_supersegment='A'
        ),
        proporz_election(
            title='Election 2',
            id='2',
            shortcode='P2',
            domain='region',
            date=date(2020, 3, 22),
            number_of_mandates=1,
            status='final',
            domain_supersegment='A'
        ),
        proporz_election(
            title='Election 3',
            id='3',
            shortcode='P3',
            domain='region',
            date=date(2020, 3, 22),
            number_of_mandates=1,
            status='final',
            domain_supersegment='B'
        ),
        proporz_election(
            title='Election 4',
            id='4',
            shortcode='P4',
            domain='region',
            date=date(2020, 3, 22),
            number_of_mandates=1,
            status='interim',
            domain_supersegment=''
        )
    ]
    session.add_all([election_compound] + elections)
    session.flush()

    election_compound.elections = elections

    assert elections[0].completed is False
    assert elections[1].completed is True
    assert elections[2].completed is True
    assert elections[3].completed is False
    assert election_compound.completed is False
    assert election_compound.progress == (1, 3)


def test_election_compound_attachments(
    test_app, explanations_pdf, upper_apportionment_pdf,
    lower_apportionment_pdf
):
    model = ElectionCompound(
        title='Legislative Elections',
        domain='canton',
        date=date(2015, 6, 14),
    )

    assert model.explanations_pdf is None
    assert model.upper_apportionment_pdf is None
    assert model.lower_apportionment_pdf is None

    del model.explanations_pdf
    del model.upper_apportionment_pdf
    del model.lower_apportionment_pdf

    model.explanations_pdf = (explanations_pdf, 'e.pdf')
    file = model.explanations_pdf
    assert file.name == 'explanations_pdf'
    assert file.reference.filename == 'e.pdf'
    assert file.reference.content_type == 'application/pdf'

    model.upper_apportionment_pdf = (upper_apportionment_pdf, 'u.pdf')
    file = model.upper_apportionment_pdf
    assert file.name == 'upper_apportionment_pdf'
    assert file.reference.filename == 'u.pdf'
    assert file.reference.content_type == 'application/pdf'

    model.lower_apportionment_pdf = (lower_apportionment_pdf, 'l.pdf')
    file = model.lower_apportionment_pdf
    assert file.name == 'lower_apportionment_pdf'
    assert file.reference.filename == 'l.pdf'
    assert file.reference.content_type == 'application/pdf'

    del model.explanations_pdf
    del model.upper_apportionment_pdf
    del model.lower_apportionment_pdf

    assert model.explanations_pdf is None
    assert model.upper_apportionment_pdf is None
    assert model.lower_apportionment_pdf is None


def test_election_compound_historical_party_strengths(session):
    first = ElectionCompound(
        title='First',
        domain='federation',
        date=date(2014, 1, 1),
        colors={'a': 'x'}
    )
    second = ElectionCompound(
        title='Second',
        domain='federation',
        date=date(2018, 1, 1),
        colors={'a': 'y', 'b': 'y'}
    )
    third = ElectionCompound(
        title='Third',
        domain='federation',
        date=date(2022, 1, 1),
        colors={'b': 'z', 'c': 'z'}
    )
    session.add(first)
    session.add(second)
    session.add(third)
    session.flush()

    assert first.historical_party_results.count() == 0
    assert second.historical_party_results.count() == 0
    assert third.historical_party_results.count() == 0
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y'}
    assert third.historical_colors == {'b': 'z', 'c': 'z'}

    # add results
    for (compound, year, party_id, domain) in (
        (first, 2014, 1, 'canton'),
        (first, 2014, 2, 'canton'),
        (first, 2014, 3, 'canton'),
        (first, 2010, 1, 'canton'),
        (first, 2010, 2, 'canton'),
        (first, 2010, 3, 'canton'),
        (second, 2022, 2, 'canton'),
        (second, 2022, 3, 'canton'),
        (second, 2018, 2, 'canton'),
        (second, 2018, 3, 'canton'),
        (second, 2018, 4, 'canton'),
        (second, 2010, 2, 'canton'),
        (second, 2010, 3, 'canton'),
        (third, 2022, 1, 'canton'),
        (third, 2022, 3, 'canton'),
        (third, 2022, 5, 'canton'),
        (third, 2022, 5, 'superregion'),
    ):
        compound.party_results.append(
            PartyResult(
                year=year,
                number_of_mandates=0,
                votes=1,
                total_votes=100,
                name_translations={'en_US': str(party_id)},
                party_id=str(party_id),
                domain=domain
            )
        )

    # no relationships yet
    assert first.historical_party_results.count() == 6
    assert second.historical_party_results.count() == 7
    assert third.historical_party_results.count() == 4
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y'}
    assert third.historical_colors == {'b': 'z', 'c': 'z'}

    # add relationships
    for (source_, target, type_) in (
        (third, second, 'historical'),
        (third, first, 'historical'),
        (second, first, 'historical'),
        (first, second, None),
        (second, third, 'historical')
    ):
        session.add(
            ElectionCompoundRelationship(
                source_id=source_.id, target_id=target.id, type=type_
            )
        )

    def extract(compound):
        return sorted(
            (result.election_compound_id, result.year, result.party_id)
            for result in compound.historical_party_results
        )

    assert extract(first) == [
        ('first', 2010, '1'),
        ('first', 2010, '2'),
        ('first', 2010, '3'),
        ('first', 2014, '1'),
        ('first', 2014, '2'),
        ('first', 2014, '3'),
    ]
    assert extract(second) == [
        ('first', 2014, '1'),
        ('first', 2014, '2'),
        ('first', 2014, '3'),
        ('second', 2010, '2'),
        ('second', 2010, '3'),
        ('second', 2018, '2'),
        ('second', 2018, '3'),
        ('second', 2018, '4'),
        ('second', 2022, '2'),
        ('second', 2022, '3'),
    ]
    assert extract(third) == [
        ('second', 2018, '2'),
        ('second', 2018, '3'),
        ('second', 2018, '4'),
        ('third', 2022, '1'),
        ('third', 2022, '3'),
        ('third', 2022, '5'),
        ('third', 2022, '5'),
    ]
    assert third.historical_party_results.filter_by(
        domain='superregion'
    ).count() == 1
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y', 'c': 'z'}
    assert third.historical_colors == {'b': 'z', 'c': 'z', 'a': 'y'}
