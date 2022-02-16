from datetime import date
from datetime import datetime
from freezegun import freeze_time
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionResult
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ListResult
from onegov.ballot import PanachageResult
from onegov.ballot import PartyResult
from onegov.ballot import ProporzElection
from onegov.ballot.models.election.election_compound import \
    ElectionCompoundAssociation
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
        status=None
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
        status=status
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

    election_result.list_results.append(
        ListResult(list_id=list_id_1, votes=520)
    )
    election_result.list_results.append(
        ListResult(list_id=list_id_2, votes=111)
    )
    election.results.append(election_result)

    list_1.panachage_results.append(
        PanachageResult(source=list_2.list_id, votes=12)
    )
    list_1.panachage_results.append(
        PanachageResult(source='99', votes=4)
    )

    return election


def test_election_compound(session):
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
    assert election_compound.completed is False
    assert election_compound.elected_candidates == []
    assert election_compound.related_link is None

    # Add two elections
    session.add(
        Election(
            title="First election",
            domain='region',
            domain_segment='First district',
            date=date(2015, 6, 14),
            number_of_mandates=1,
            last_result_change=datetime(2015, 6, 14, 14, 1, tzinfo=UTC)
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

    assert election_compound.number_of_mandates == 3
    assert election_compound.counted is False
    assert election_compound.progress == (0, 2)
    assert election_compound.counted_entities == []
    assert election_compound.allocated_mandates == 0
    assert election_compound.has_results == False
    assert election_compound.completed == False
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
    assert election_compound.has_results == False
    assert election_compound.completed == False

    # Set results as counted
    session.query(ElectionResult).first().counted = True
    assert election_compound.counted is False
    assert election_compound.progress == (0, 2)
    assert election_compound.counted_entities == []
    assert election_compound.allocated_mandates == 0
    assert election_compound.has_results == True
    assert election_compound.completed == False

    for result in session.query(ElectionResult):
        result.counted = True
    assert election_compound.counted is True
    assert election_compound.progress == (2, 2)
    assert election_compound.counted_entities == [
        'First district', 'Second district'
    ]
    assert election_compound.allocated_mandates == 0
    assert election_compound.completed == True

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
        owner=election_compound.id,
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name='Libertarian',
        color='black'
    )
    session.add(party_result)
    session.flush()
    assert election_compound.party_results.one() == party_result

    # Add panachage results
    panachage_result = PanachageResult(
        owner=election_compound.id,
        source='A',
        target='B',
        votes=0,
    )
    session.add(panachage_result)
    session.flush()
    assert election_compound.panachage_results.one() == panachage_result

    election_compound.last_result_change = election_compound.timestamp()

    # Clear results
    election_compound.clear_results()
    assert election_compound.last_result_change.date() == date(2015, 6, 14)
    assert election_compound.party_results.first() is None
    assert election_compound.panachage_results.first() is None

    election = session.query(Election).filter_by(title="First election").one()
    election.clear_results()
    election_compound.clear_results()
    assert election_compound.last_result_change is None


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
    session.add(majorz_election())
    session.add(proporz_election())
    session.flush()
    election_compound = session.query(ElectionCompound).one()
    election_compound.title_translations['it_CH'] = 'Elezioni'

    assert election_compound.export() == []

    election_compound.elections = session.query(Election).filter_by(
        id='majorz'
    ).all()
    session.flush()
    exports = election_compound.export()
    assert exports[0] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_title_rm_CH': '',
        'compound_date': '2015-06-14',
        'compound_mandates': 1,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_title_rm_CH': '',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
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
        'candidate_votes': 111
    }
    assert exports[1] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_title_rm_CH': '',
        'compound_date': '2015-06-14',
        'compound_mandates': 1,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_title_rm_CH': '',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
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
        'candidate_votes': 520
    }

    election_compound.elections = session.query(Election).all()
    session.flush()
    exports = election_compound.export()

    assert exports[0] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_title_rm_CH': '',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Proporz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_title_rm_CH': '',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'proporz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
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
        'list_number_of_mandates': 0,
        'list_votes': 111,
        'list_connection': 'A.1',
        'list_connection_parent': 'A',
        'candidate_family_name': 'Nahasapeemapetilon',
        'candidate_first_name': 'Apu',
        'candidate_id': '2',
        'candidate_elected': False,
        'candidate_party': 'Democratic Party',
        'candidate_votes': 111,
        'panachage_votes_from_list_1': None,
        'panachage_votes_from_list_2': None,
        'panachage_votes_from_list_99': None
    }

    assert exports[1] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_title_rm_CH': '',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Proporz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_title_rm_CH': '',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'proporz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
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
        'list_number_of_mandates': 1,
        'list_votes': 520,
        'list_connection': None,
        'list_connection_parent': None,
        'candidate_family_name': 'Quimby',
        'candidate_first_name': 'Joe',
        'candidate_id': '1',
        'candidate_elected': True,
        'candidate_party': 'Republican Party',
        'candidate_votes': 520,
        'panachage_votes_from_list_1': None,
        'panachage_votes_from_list_2': 12,
        'panachage_votes_from_list_99': 4
    }

    assert exports[2] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_title_rm_CH': '',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_title_rm_CH': '',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
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
        'candidate_votes': 111
    }

    assert exports[3] == {
        'compound_title_de_CH': 'Elections',
        'compound_title_fr_CH': '',
        'compound_title_it_CH': 'Elezioni',
        'compound_title_rm_CH': '',
        'compound_date': '2015-06-14',
        'compound_mandates': 2,
        'election_title_de_CH': 'Majorz',
        'election_title_fr_CH': '',
        'election_title_it_CH': 'Elezione',
        'election_title_rm_CH': '',
        'election_date': '2015-06-14',
        'election_domain': 'federation',
        'election_type': 'majorz',
        'election_mandates': 1,
        'election_absolute_majority': 144,
        'election_status': 'unknown',
        'entity_district': '',
        'entity_name': 'name',
        'entity_id': 1,
        'entity_counted': True,
        'entity_eligible_voters': 1000,
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

    assert election_compound.export_parties() == []

    # Add party results
    election_compound.party_results.append(
        PartyResult(
            number_of_mandates=0,
            votes=0,
            voters_count=1,
            total_votes=100,
            name='Libertarian',
            color='black',
            year=2012
        )
    )
    election_compound.party_results.append(
        PartyResult(
            number_of_mandates=2,
            votes=2,
            voters_count=3,
            total_votes=50,
            name='Libertarian',
            color='black',
            year=2016
        )
    )
    election_compound.party_results.append(
        PartyResult(
            number_of_mandates=1,
            votes=1,
            voters_count=2,
            total_votes=100,
            name='Conservative',
            color='red',
            year=2012
        )
    )
    election_compound.party_results.append(
        PartyResult(
            number_of_mandates=3,
            votes=3,
            voters_count=4,
            total_votes=50,
            name='Conservative',
            color='red',
            year=2016
        )
    )

    assert election_compound.export_parties() == [
        {
            'year': 2016,
            'name': 'Conservative',
            'id': 0,
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': 4,
        }, {
            'year': 2016,
            'name': 'Libertarian',
            'id': 1,
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': 3,
        }, {
            'year': 2012,
            'name': 'Conservative',
            'id': 0,
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': 2,
        }, {
            'year': 2012,
            'name': 'Libertarian',
            'id': 1,
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': 1,
        }
    ]

    # Add panachage results
    for idx, source in enumerate(('Conservative', 'Libertarian', 'Other', '')):
        election_compound.panachage_results.append(
            PanachageResult(
                target='Conservative',
                source=source,
                votes=idx + 1
            )
        )
    election_compound.panachage_results.append(
        PanachageResult(
            target='Libertarian',
            source='Conservative',
            votes=5,
        )
    )
    assert election_compound.export_parties() == [
        {
            'year': 2016,
            'name': 'Conservative',
            'id': 0,
            'color': 'red',
            'mandates': 3,
            'total_votes': 50,
            'votes': 3,
            'voters_count': 4,
            'panachage_votes_from_0': 1,
            'panachage_votes_from_1': 2,
            'panachage_votes_from_2': 3,
            'panachage_votes_from_999': 4,
        }, {
            'year': 2016,
            'name': 'Libertarian',
            'id': 1,
            'color': 'black',
            'mandates': 2,
            'total_votes': 50,
            'votes': 2,
            'voters_count': 3,
            'panachage_votes_from_0': 5,
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'color': '',
            'mandates': '',
            'name': 'Other',
            'id': 2,
            'total_votes': '',
            'votes': '',
            'voters_count': '',
            'year': 2016,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'year': 2012,
            'name': 'Conservative',
            'id': 0,
            'color': 'red',
            'mandates': 1,
            'total_votes': 100,
            'votes': 1,
            'voters_count': 2,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'year': 2012,
            'name': 'Libertarian',
            'id': 1,
            'color': 'black',
            'mandates': 0,
            'total_votes': 100,
            'votes': 0,
            'voters_count': 1,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }, {
            'color': '',
            'mandates': '',
            'name': 'Other',
            'id': 2,
            'total_votes': '',
            'votes': '',
            'voters_count': '',
            'year': 2012,
            'panachage_votes_from_0': '',
            'panachage_votes_from_1': '',
            'panachage_votes_from_2': '',
            'panachage_votes_from_999': '',
        }
    ]


def test_election_compound_rename(session):
    session.add(majorz_election())
    session.add(proporz_election())
    session.flush()

    election_compound = ElectionCompound(
        title='Elections',
        id='elerctions',
        domain='canton',
        date=date(2015, 6, 14),
    )
    election_compound.elections = session.query(Election).all()
    session.add(election_compound)
    session.flush()

    query = session.query(
        ElectionCompoundAssociation.election_compound_id.distinct()
    )
    assert query.one()[0] == 'elerctions'

    election_compound.id = 'elections'
    assert query.one()[0] == 'elections'
    assert len(election_compound.elections) == 2

    session.flush()
    assert query.one()[0] == 'elections'
    assert len(election_compound.elections) == 2


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


def test_list_results(session):
    election_compound = ElectionCompound(
        title='Elections',
        domain='canton',
        date=date(2015, 6, 14),
    )
    session.add(election_compound)
    session.flush()

    assert election_compound.get_list_results() == []
    elections = [
        proporz_election(id='1', number_of_mandates=1),
        proporz_election(id='2', number_of_mandates=2),
        proporz_election(id='3', number_of_mandates=3)
    ]
    for election in elections:
        session.add(election)
    election_compound.elections = elections
    session.flush()

    # Not Doppelter Pukelsheim
    assert election_compound.get_list_results() == []

    # Doppelter Pukelsheim with manual completion
    election_compound.pukelsheim = True
    election_compound.completes_manually = True
    election_compound.manually_completed = False
    assert election_compound.get_list_results() == [
        ('Quimby Again!', 3, 953),  # 520 / 1 + 520 / 2 + 520 / 3
        ('Kwik-E-Major', 0, 204)  # 111 / 1 + 111/2 + 111/3
    ]

    # Add another list
    list_id = uuid4()
    list_ = List(
        id=list_id,
        list_id='3',
        number_of_mandates=5,
        name='Burns burns!',
    )
    list_result = ListResult(
        list_id=list_id,
        votes=200
    )
    election_result = ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
    )
    election_result.list_results.append(list_result)
    elections[0].lists.append(list_)
    elections[0].results.append(election_result)
    session.flush()

    assert election_compound.get_list_results() == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
        ('Burns burns!', 5, 200)  # 200 + 0 / 2 + 0 / 3
    ]

    # Test optional parameters
    # ... limit
    assert election_compound.get_list_results(limit=0) == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
        ('Burns burns!', 5, 200)
    ]
    assert election_compound.get_list_results(limit=None) == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
        ('Burns burns!', 5, 200)
    ]
    assert election_compound.get_list_results(limit=-5) == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
        ('Burns burns!', 5, 200)
    ]
    assert election_compound.get_list_results(limit=2) == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
    ]

    # ... names
    assert election_compound.get_list_results(names=[]) == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
        ('Burns burns!', 5, 200)
    ]
    assert election_compound.get_list_results(names=None) == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
        ('Burns burns!', 5, 200)
    ]
    assert election_compound.get_list_results(
        names=['Quimby Again!', 'Kwik-E-Major', 'All others']
    ) == [
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204),
    ]

    # ... manually completed
    election_compound.manually_completed = True
    assert election_compound.get_list_results() == [
        ('Burns burns!', 5, 200),
        ('Quimby Again!', 3, 953),
        ('Kwik-E-Major', 0, 204)
    ]

    # ... limit & names & order_by
    assert election_compound.get_list_results(
        limit=1,
        names=['Quimby Again!'],
    ) == [
        ('Quimby Again!', 3, 953),
    ]
