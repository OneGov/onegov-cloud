from datetime import date
from datetime import datetime
from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundPart
from onegov.ballot import ElectionResult
from onegov.ballot import PartyResult
from pytz import UTC


def test_election_compound_part_model(session):
    session.add(
        ElectionCompound(
            title='Elections',
            domain='canton',
            domain_elections='region',
            date=date(2015, 6, 14),
            horizontal_party_strengths=True,
            show_party_strengths=True
        )
    )
    session.flush()
    compound = session.query(ElectionCompound).one()
    part = ElectionCompoundPart(compound, 'superregion', 'First Superregion')

    assert part.date == date(2015, 6, 14)
    assert part.completes_manually is False
    assert part.manually_completed is False
    assert part.completed is False
    assert part.last_result_change is None
    assert part.last_modified
    assert part.domain_elections == 'region'
    assert part.colors == {}
    assert part.voters_counts is False
    assert part.exact_voters_counts is False
    assert part.horizontal_party_strengths is True
    assert part.show_party_strengths is True
    assert part.title == 'Elections First Superregion'
    assert part.title_translations == {'de_CH': 'Elections First Superregion'}
    assert part.elections == []
    assert part.session
    assert part.progress == (0, 0)
    assert part.party_results.first() is None
    assert part.has_results is False
    assert part.number_of_mandates == 0
    assert part.allocated_mandates == 0
    assert part.counted is True
    assert part.counted_entities == []
    assert part.results == []

    # Add two elections
    last_result_change = datetime(2015, 6, 14, 14, 1, tzinfo=UTC)
    session.add(
        Election(
            title="First election",
            domain='region',
            domain_segment='First Region',
            domain_supersegment='First Superregion',
            date=date(2015, 6, 14),
            number_of_mandates=1,
            last_result_change=last_result_change
        )
    )
    session.add(
        Election(
            title="Second election",
            domain='region',
            domain_segment='Second Region',
            domain_supersegment='Second Superregion',
            date=date(2015, 6, 14),
            number_of_mandates=2,
        )
    )
    session.flush()
    compound.elections = session.query(Election).all()
    session.flush()

    assert part.completed is False
    assert part.last_result_change == last_result_change
    assert part.last_modified
    assert [e.id for e in part.elections] == ['first-election']
    assert part.progress == (0, 1)
    assert part.party_results.first() is None
    assert part.has_results is False
    assert part.number_of_mandates == 1
    assert part.allocated_mandates == 0
    assert part.counted is False
    assert part.counted_entities == []
    assert [r.__dict__ for r in part.results] == [
        {
            'accounted_ballots': 0,
            'accounted_votes': 0,
            'blank_ballots': 0,
            'counted': False,
            'counted_eligible_voters': 0,
            'counted_received_ballots': 0,
            'domain_segment': 'First Region',
            'domain_supersegment': 'First Superregion',
            'eligible_voters': 0,
            'expats': 0,
            'invalid_ballots': 0,
            'received_ballots': 0,
            'turnout': 0
        }
    ]

    # Add results and candidates
    candidates = (('Paul', 'Peter'), ('Max', 'Miro'))
    for index, election in enumerate(compound.elections):
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

    assert part.completed is False
    assert part.progress == (0, 1)
    assert part.party_results.first() is None
    assert part.has_results is False
    assert part.number_of_mandates == 1
    assert part.allocated_mandates == 0
    assert part.counted is False
    assert part.counted_entities == []
    assert [r.__dict__ for r in part.results] == [
        {
            'accounted_ballots': 258,
            'accounted_votes': 216,
            'blank_ballots': 12,
            'counted': False,
            'counted_eligible_voters': 0,
            'counted_received_ballots': 0,
            'domain_segment': 'First Region',
            'domain_supersegment': 'First Superregion',
            'eligible_voters': 400,
            'expats': 40,
            'invalid_ballots': 30,
            'received_ballots': 300,
            'turnout': 0
        },
    ]

    # Set results as counted
    part.elections[0].results[0].counted = True
    assert part.completed is False
    assert part.counted is False
    assert part.progress == (0, 1)
    assert part.counted_entities == []
    assert part.allocated_mandates == 0
    assert part.has_results == True
    assert [r.__dict__ for r in part.results] == [
        {
            'accounted_ballots': 258,
            'accounted_votes': 216,
            'blank_ballots': 12,
            'counted': False,
            'counted_eligible_voters': 200,
            'counted_received_ballots': 150,
            'domain_segment': 'First Region',
            'domain_supersegment': 'First Superregion',
            'eligible_voters': 400,
            'expats': 40,
            'invalid_ballots': 30,
            'received_ballots': 300,
            'turnout': 75.0
        }
    ]

    part.elections[0].results[1].counted = True
    assert part.completed is True
    assert part.counted is True
    assert part.progress == (1, 1)
    assert part.counted_entities == ['First Region']
    assert part.allocated_mandates == 0
    assert part.has_results == True
    assert [r.__dict__ for r in part.results] == [
        {
            'accounted_ballots': 258,
            'accounted_votes': 216,
            'blank_ballots': 12,
            'counted': True,
            'counted_eligible_voters': 400,
            'counted_received_ballots': 300,
            'domain_segment': 'First Region',
            'domain_supersegment': 'First Superregion',
            'eligible_voters': 400,
            'expats': 40,
            'invalid_ballots': 30,
            'received_ballots': 300,
            'turnout': 75.0
        }
    ]

    # Add party results
    session.add(
        PartyResult(
            owner=compound.id,
            domain='canton',
            domain_segment='',
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='1'
        )
    )
    session.add(
        PartyResult(
            owner=compound.id,
            domain='superregion',
            domain_segment='First Superregion',
            number_of_mandates=0,
            votes=20,
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='1'
        )
    )
    session.add(
        PartyResult(
            owner=compound.id,
            domain='superregion',
            domain_segment='Second Superregion',
            number_of_mandates=0,
            votes=30,
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='1'
        )
    )
    session.flush()
    assert part.party_results.one().votes == 20

    # Clear results
    compound.clear_results()
    assert part.last_result_change is None
    assert part.party_results.first() is None
