from datetime import date
from freezegun import freeze_time
from onegov.ballot import Candidate
from onegov.ballot import CandidateResult
from onegov.ballot import Election
from onegov.ballot import ElectionAssociation
from onegov.ballot import ElectionResult
from uuid import uuid4


def majorz_election():
    eid = uuid4()
    cid = uuid4()
    election = Election(
        title='Election',
        domain='canton',
        date=date(2017, 1, 1),
        status='interim',
        absolute_majority=10000
    )
    candidate = Candidate(
        id=cid,
        candidate_id='0',
        family_name='X',
        first_name='Y',
        elected=False
    )
    election_result = ElectionResult(
        id=eid,
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=100,
        received_ballots=2,
        blank_ballots=3,
        invalid_ballots=4,
        blank_votes=5,
        invalid_votes=6
    )
    candidate_result = CandidateResult(
        election_result_id=eid,
        candidate_id=cid,
        votes=0
    )
    election_result.candidate_results.append(candidate_result)
    election.candidates.append(candidate)
    election.results.append(election_result)
    return election


def test_election_create_all_models(session):
    election = Election(
        title="Election",
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    candidate = Candidate(
        candidate_id="0",
        family_name="Quimby",
        first_name="Joe",
        elected=False,
        election_id=election.id,
    )

    session.add(candidate)
    session.flush()

    election_result = ElectionResult(
        election_id=election.id,
        name='name',
        entity_id=1000,
        counted=False,
        eligible_voters=0,
        received_ballots=0,
        blank_ballots=0,
        invalid_ballots=0,
        blank_votes=0,
        invalid_votes=0
    )

    session.add(election_result)
    session.flush()

    candidate_result = CandidateResult(
        election_result_id=election_result.id,
        candidate_id=candidate.id,
        votes=0
    )

    session.add(candidate_result)
    session.flush()

    assert election.candidates.one() == candidate
    assert election.results.one() == election_result

    assert candidate.results.one() == candidate_result
    assert candidate.election == election

    assert election_result.candidate_results.one() == candidate_result
    assert election_result.election == election

    assert candidate_result.election_result == election_result
    assert candidate_result.candidate == candidate

    session.delete(election)
    session.flush()

    assert session.query(Candidate).all() == []
    assert session.query(CandidateResult).all() == []
    assert session.query(Election).all() == []
    assert session.query(ElectionResult).all() == []


def test_election_id_generation(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.id == 'legislative-election'

    election = Election(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.id == 'legislative-election-1'

    election = Election(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.id == 'legislative-election-2'


def test_election_summarized_properties(session):
    election = Election(
        title="Election",
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=2
    )
    for x in range(1, 4):
        election.results.append(
            ElectionResult(
                name='name',
                entity_id=x,
                counted=True,
                eligible_voters=100 * x,
                received_ballots=80 * x,
                blank_ballots=4 * x,
                invalid_ballots=3 * x,
                blank_votes=2 * x,
                invalid_votes=x
            )
        )

    session.add(election)
    session.flush()

    assert election.eligible_voters == 600
    assert election.received_ballots == 480
    assert election.accounted_ballots == 438
    assert election.blank_ballots == 24
    assert election.invalid_ballots == 18
    assert election.accounted_votes == 858


def test_election_derived_properties(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )
    election.results.append(ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=100,
        received_ballots=50,
        blank_ballots=2,
        invalid_ballots=5,
        blank_votes=4,
        invalid_votes=3
    ))
    election.results.append(ElectionResult(
        name='name',
        entity_id=2,
        counted=True,
        eligible_voters=200,
        received_ballots=150,
        blank_ballots=6,
        invalid_ballots=15,
        blank_votes=12,
        invalid_votes=9
    ))

    session.add(election)
    session.flush()

    assert election.results[0].unaccounted_ballots == 7
    assert election.results[0].accounted_ballots == 43
    assert election.results[0].turnout == 50.0
    assert election.results[1].unaccounted_ballots == 21
    assert election.results[1].accounted_ballots == 129
    assert election.results[1].turnout == 75.0
    assert election.unaccounted_ballots == 28
    assert election.accounted_ballots == 172
    assert int(election.turnout) == 66
    assert session.query(
        Election.eligible_voters,
        Election.received_ballots,
        Election.accounted_ballots,
        Election.blank_ballots,
        Election.invalid_ballots
    ).one() == (300, 200, 172, 8, 20)


def test_election_counted(session):
    election = Election(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.counted is False
    assert election.progress == (0, 0)

    election.results.append(ElectionResult(
        name='name',
        entity_id=1,
        counted=False,
        eligible_voters=200,
        received_ballots=150,
        blank_ballots=6,
        invalid_ballots=15,
        blank_votes=12,
        invalid_votes=9
    ))

    assert election.counted is False
    assert election.progress == (0, 1)

    election.results.append(ElectionResult(
        name='name',
        entity_id=2,
        counted=True,
        eligible_voters=200,
        received_ballots=150,
        blank_ballots=6,
        invalid_ballots=15,
        blank_votes=12,
        invalid_votes=9
    ))

    assert election.counted is False
    assert election.progress == (1, 2)

    for result in election.results:
        result.counted = True

    assert election.counted is True
    assert election.progress == (2, 2)


def test_election_last_change(session):
    # Add the election
    with freeze_time("2001-01-01"):
        election = Election(
            title='Legislative Election',
            domain='federation',
            date=date(2015, 6, 14),
        )
        session.add(election)
        session.flush()

    assert election.last_modified.isoformat().startswith('2001')
    assert election.last_result_change is None

    # Add a result
    with freeze_time("2002-01-01"):
        election.results.append(ElectionResult(
            name='name',
            entity_id=1,
            counted=True,
            eligible_voters=100,
            received_ballots=50,
            blank_ballots=2,
            invalid_ballots=5,
            blank_votes=4,
            invalid_votes=3
        ))
        session.flush()

    assert election.last_modified.isoformat().startswith('2002')
    assert election.last_result_change.isoformat().startswith('2002')

    # Add another result
    with freeze_time("2003-01-01"):
        election.results.append(ElectionResult(
            name='name',
            entity_id=2,
            counted=True,
            eligible_voters=200,
            received_ballots=150,
            blank_ballots=6,
            invalid_ballots=15,
            blank_votes=12,
            invalid_votes=9
        ))
        session.flush()

    # Add a candidate
    with freeze_time("2004-01-01"):
        candidate = Candidate(
            elected=True,
            candidate_id='1',
            family_name='Quimby',
            first_name='Joe'
        )
        election.candidates.append(candidate)
        session.flush()

    assert election.last_modified.isoformat().startswith('2004')
    assert election.last_result_change.isoformat().startswith('2003')

    # Add candidate results
    with freeze_time("2005-01-01"):
        election.results.first().candidate_results.append(
            CandidateResult(candidate_id=candidate.id, votes=520)
        )
        session.flush()

    assert election.last_modified.isoformat().startswith('2005')
    assert election.last_result_change.isoformat().startswith('2005')

    # Change a result
    with freeze_time("2006-01-01"):
        election.results.first().blank_ballots = 7
        session.flush()

    assert election.last_modified.isoformat().startswith('2006')
    assert election.last_result_change.isoformat().startswith('2006')

    # Change the candidate result
    with freeze_time("2007-01-01"):
        election.candidates.first().results.first().votes = 510
        session.flush()

    assert election.last_modified.isoformat().startswith('2007')
    assert election.last_result_change.isoformat().startswith('2007')

    # Change the candidate
    with freeze_time("2008-01-01"):
        election.candidates.first().elected = False
        session.flush()

    assert election.last_modified.isoformat().startswith('2008')
    assert election.last_result_change.isoformat().startswith('2007')

    # Change the election
    with freeze_time("2009-01-01"):
        election.domain = 'canton'
        session.flush()

    assert election.last_modified.isoformat().startswith('2009')
    assert election.last_result_change.isoformat().startswith('2007')


def test_election_results(session):
    election = Election(
        title='Election',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )

    session.add(election)
    session.flush()

    assert sorted((c.votes for c in election.candidates)) == []

    # Add two entities
    election_result_1 = ElectionResult(
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
    election_result_2 = ElectionResult(
        name='name',
        entity_id=2,
        counted=True,
        eligible_voters=100,
        received_ballots=50,
        blank_ballots=1,
        invalid_ballots=0,
        blank_votes=8,
        invalid_votes=1
    )
    election.results.append(election_result_1)
    election.results.append(election_result_2)

    session.flush()

    assert sorted((c.votes for c in election.candidates)) == []

    # Add 5 candidates
    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        family_name='Quimby',
        first_name='Joe',
        party='Republican Party',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        family_name='Nahasapeemapetilon',
        first_name='Apu',
        party='Democratic Party',
    )
    candidate_3 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='3',
        family_name='Flanders',
        first_name='Ned',
        party='Republican Party',
    )
    candidate_4 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='4',
        family_name='Lovejoy',
        first_name='Tim',
        party='Republican Party',
    )
    candidate_5 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='5',
        family_name='Smithers',
        first_name='Waylon',
        party='Democratic Party',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)
    election.candidates.append(candidate_3)
    election.candidates.append(candidate_4)
    election.candidates.append(candidate_5)

    # Add 4 candidate results to the first entity
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=520,
        )
    )
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_2.id,
            votes=111
        )
    )
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_3.id,
            votes=20
        )
    )
    election_result_1.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_4.id,
            votes=1
        )
    )

    # Add 2 candidate results to the second entity
    election_result_2.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=20
        )
    )
    election_result_2.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_5.id,
            votes=5
        )
    )

    session.flush()

    expected = [1, 5, 20, 111, 540]
    assert sorted((c.votes for c in election.candidates)) == expected
    votes = session.query(Candidate.votes, Candidate.family_name)
    votes = votes.order_by(Candidate.votes)
    assert [vote[0] for vote in votes] == [1, 5, 20, 111, 540]

    assert election.number_of_mandates == election.allocated_mandates
    assert election.elected_candidates == [('Joe', 'Quimby')]


def test_election_export(session):
    election = Election(
        title='Wahl',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1,
        absolute_majority=144
    )
    election.title_translations['it_CH'] = 'Elezione'

    candidate_1 = Candidate(
        id=uuid4(),
        elected=True,
        candidate_id='1',
        family_name='Quimby',
        first_name='Joe',
        party='Republican Party',
    )
    candidate_2 = Candidate(
        id=uuid4(),
        elected=False,
        candidate_id='2',
        family_name='Nahasapeemapetilon',
        first_name='Apu',
        party='Democratic Party',
    )
    election.candidates.append(candidate_1)
    election.candidates.append(candidate_2)

    session.add(election)
    session.flush()

    assert election.export() == []

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
        CandidateResult(
            candidate_id=candidate_1.id,
            votes=520,
        )
    )
    election_result.candidate_results.append(
        CandidateResult(
            candidate_id=candidate_2.id,
            votes=111
        )
    )
    election.results.append(election_result)

    session.flush()

    assert election.export() == [
        {
            'election_title_de_CH': 'Wahl',
            'election_title_it_CH': 'Elezione',
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
            'candidate_votes': 111,
        }, {
            'election_title_de_CH': 'Wahl',
            'election_title_it_CH': 'Elezione',
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
            'candidate_votes': 520,
        }
    ]


def test_election_meta_data(session):
    election = Election(
        title='Election',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )
    assert not election.meta

    session.add(election)
    session.flush()

    assert not election.meta

    election.meta['a'] = 1
    assert election.meta['a'] == 1

    session.flush()
    election.meta['b'] = 2
    assert election.meta['a'] == 1
    assert election.meta['b'] == 2


def test_election_status(session):
    election = Election(
        title='Election',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )
    session.add(election)
    session.flush()

    assert election.status is None
    assert election.completed is False

    # Set status
    election.status = 'unknown'
    session.flush()
    assert election.status == 'unknown'

    election.status = 'interim'
    session.flush()
    assert election.status == 'interim'

    election.status = 'final'
    session.flush()
    assert election.status == 'final'

    election.status = None
    session.flush()
    assert election.status is None

    # Test completed calcuation
    # ... empty election
    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        election.status = status
        assert election.completed == completed

    # ... election with some results
    election.results.append(ElectionResult(
        name='name',
        entity_id=1,
        counted=True,
        eligible_voters=200,
        received_ballots=150,
        blank_ballots=6,
        invalid_ballots=15,
        blank_votes=12,
        invalid_votes=9
    ))
    election.results.append(ElectionResult(
        name='name',
        entity_id=2,
        counted=False,
        eligible_voters=200,
        received_ballots=150,
        blank_ballots=6,
        invalid_ballots=15,
        blank_votes=12,
        invalid_votes=9
    ))

    for status, completed in (
        (None, False), ('unknown', False), ('interim', False), ('final', True)
    ):
        election.status = status
        assert election.completed == completed

    # ... vote with all results
    for result in election.results:
        result.counted = True
    for status, completed in (
        (None, True), ('unknown', True), ('interim', False), ('final', True)
    ):
        election.status = status
        assert election.completed == completed


def test_election_clear_results(session):
    election = majorz_election()
    session.add(election)
    session.flush()

    election.clear_results()

    assert election.absolute_majority is None
    assert election.status is None
    assert election.candidates.all() == []
    assert election.results.all() == []

    assert session.query(Candidate).first() is None
    assert session.query(CandidateResult).first() is None
    assert session.query(ElectionResult).first() is None


def test_election_has_results(session):
    election = Election(
        title='Election',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )
    session.add(election)
    session.flush()

    assert election.has_results is False

    election.results.append(
        ElectionResult(
            name='name',
            entity_id=1,
            counted=False,
            eligible_voters=100,
            received_ballots=2,
            blank_ballots=3,
            invalid_ballots=4,
            blank_votes=5,
            invalid_votes=6
        )
    )

    assert election.has_results is False

    election.results.one().counted = True

    assert election.has_results is True


def test_related_elections(session):
    first = Election(
        title='First',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )
    second = Election(
        title='Second',
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=1
    )
    session.add(first)
    session.add(second)
    session.flush()
    assert first.related_elections.all() == []
    assert first.referencing_elections.all() == []
    assert second.related_elections.all() == []
    assert second.referencing_elections.all() == []

    first.related_elections.append(ElectionAssociation(target_id=second.id))
    session.flush()
    assert first.related_elections.one().source_id == 'first'
    assert first.related_elections.one().target_id == 'second'
    assert first.referencing_elections.all() == []
    assert second.related_elections.all() == []
    assert second.referencing_elections.one().source_id == 'first'
    assert second.referencing_elections.one().target_id == 'second'

    second.related_elections.append(ElectionAssociation(target_id=first.id))
    session.flush()
    assert first.related_elections.one().source_id == 'first'
    assert first.related_elections.one().target_id == 'second'
    assert first.referencing_elections.one().source_id == 'second'
    assert first.referencing_elections.one().target_id == 'first'
    assert second.related_elections.one().source_id == 'second'
    assert second.related_elections.one().target_id == 'first'
    assert second.referencing_elections.one().source_id == 'first'
    assert second.referencing_elections.one().target_id == 'second'

    session.delete(second)
    session.flush()
    assert first.related_elections.all() == []
    assert first.referencing_elections.all() == []
    assert session.query(ElectionAssociation).all() == []

    first.related_elections.append(ElectionAssociation(target_id=first.id))
    session.flush()
    assert first.related_elections.one().source_id == 'first'
    assert first.related_elections.one().target_id == 'first'
    assert first.referencing_elections.one().source_id == 'first'
    assert first.referencing_elections.one().target_id == 'first'

    session.delete(first)
    session.flush()
    assert session.query(ElectionAssociation).all() == []


def test_election_rename(session):
    election = majorz_election()
    session.add(election)
    session.flush()

    session.query(Candidate).one().election_id == 'election'
    session.query(ElectionResult).one().election_id == 'election'

    election.id = 'elerction'
    session.flush()

    session.query(Candidate).one().election_id == 'elerction'
    session.query(ElectionResult).one().election_id == 'elerction'
