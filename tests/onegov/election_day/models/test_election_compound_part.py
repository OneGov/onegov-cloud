from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal
from onegov.election_day.models import Candidate
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundPart
from onegov.election_day.models import ElectionCompoundRelationship
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import PartyResult
from pytz import UTC


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_election_compound_part_model(session: Session) -> None:
    session.add(
        ElectionCompound(
            title='Elections',
            short_title='E',
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

    assert part == ElectionCompoundPart(
        compound, 'superregion', 'First Superregion'
    )
    assert part != None
    assert part != []
    assert part != ''
    assert part != ElectionCompoundPart(
        None, 'superregion', 'First Superregion'  # type: ignore[arg-type]
    )
    assert part != ElectionCompoundPart(
        compound, 'superregion', 'Second Superregion'
    )
    assert part != ElectionCompoundPart(
        compound, 'region', 'First Superregion'
    )

    assert part.date == date(2015, 6, 14)
    assert part.completes_manually is False
    assert part.manually_completed is False
    assert part.pukelsheim is False
    assert part.completed is False
    assert part.elected_candidates == []
    assert part.last_result_change is None
    assert part.last_change
    assert part.last_modified
    assert part.domain_elections == 'region'
    assert part.colors == {}
    assert part.voters_counts is False
    assert part.exact_voters_counts is False
    assert part.horizontal_party_strengths is True
    assert part.show_party_strengths is True
    assert part.title == 'Elections First Superregion'
    assert part.short_title == 'E First Superregion'
    assert part.title_translations == {'de_CH': 'Elections First Superregion'}
    assert part.short_title_translations == {'de_CH': 'E First Superregion'}
    assert part.elections == []
    assert part.progress == (0, 0)
    assert part.party_results == []
    assert part.has_results is False
    assert part.has_party_results is False
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

    # undo mypy narrowing
    part = part
    assert part.completed is False
    assert part.elected_candidates == []
    assert part.last_result_change == last_result_change
    assert part.last_change
    assert part.last_modified
    assert [e.id for e in part.elections] == ['first-election']
    assert part.progress == (0, 1)
    assert part.party_results == []
    assert part.has_results is False
    assert part.has_party_results is False
    assert part.number_of_mandates == 1
    assert part.allocated_mandates == 0
    assert part.counted is False
    assert part.counted_entities == []
    assert part.results[0].accounted_ballots == 0
    assert part.results[0].accounted_votes == 0
    assert part.results[0].blank_ballots == 0
    assert part.results[0].counted == False
    assert part.results[0].domain_segment == 'First Region'
    assert part.results[0].domain_supersegment == 'First Superregion'
    assert part.results[0].eligible_voters == 0
    assert part.results[0].expats == 0
    assert part.results[0].invalid_ballots == 0
    assert part.results[0].received_ballots == 0
    assert part.results[0].turnout == 0
    assert part.totals.accounted_ballots == 0
    assert part.totals.accounted_votes == 0
    assert part.totals.blank_ballots == 0
    assert part.totals.eligible_voters == 0
    assert part.totals.expats == 0
    assert part.totals.invalid_ballots == 0
    assert part.totals.received_ballots == 0
    assert part.totals.turnout == 0

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
    assert part.elected_candidates == []
    assert part.progress == (0, 1)
    assert part.party_results == []
    assert part.has_results is False
    assert part.has_party_results is False
    assert part.number_of_mandates == 1
    assert part.allocated_mandates == 0
    assert part.counted is False
    assert part.counted_entities == []
    assert part.results[0].accounted_ballots == 258
    assert part.results[0].accounted_votes == 216
    assert part.results[0].blank_ballots == 12
    assert part.results[0].counted == False
    assert part.results[0].domain_segment == 'First Region'
    assert part.results[0].domain_supersegment == 'First Superregion'
    assert part.results[0].eligible_voters == 400
    assert part.results[0].expats == 40
    assert part.results[0].invalid_ballots == 30
    assert part.results[0].received_ballots == 300
    assert part.results[0].turnout == 75.0
    assert part.totals.accounted_ballots == 0
    assert part.totals.accounted_votes == 0
    assert part.totals.blank_ballots == 0
    assert part.totals.eligible_voters == 0
    assert part.totals.expats == 0
    assert part.totals.invalid_ballots == 0
    assert part.totals.received_ballots == 0
    assert part.totals.turnout == 0

    # Set results as counted
    part.elections[0].results[0].counted = True
    # undo mypy narrowing
    part = part
    assert part.completed is False
    assert part.elected_candidates == []
    assert part.counted is False
    assert part.progress == (0, 1)
    assert part.counted_entities == []
    assert part.allocated_mandates == 0
    assert part.has_results is True
    assert part.results[0].accounted_ballots == 258
    assert part.results[0].accounted_votes == 216
    assert part.results[0].blank_ballots == 12
    assert part.results[0].counted == False
    assert part.results[0].domain_segment == 'First Region'
    assert part.results[0].domain_supersegment == 'First Superregion'
    assert part.results[0].eligible_voters == 400
    assert part.results[0].expats == 40
    assert part.results[0].invalid_ballots == 30
    assert part.results[0].received_ballots == 300
    assert part.results[0].turnout == 75.0
    assert part.totals.accounted_ballots == 0
    assert part.totals.accounted_votes == 0
    assert part.totals.blank_ballots == 0
    assert part.totals.eligible_voters == 0
    assert part.totals.expats == 0
    assert part.totals.invalid_ballots == 0
    assert part.totals.received_ballots == 0
    assert part.totals.turnout == 0

    part.elections[0].results[1].counted = True
    part.elections[0].candidates[0].elected = True
    # undo mypy narrowing
    part = part
    assert part.completed is True
    assert part.elected_candidates == [('Peter', 'Paul')]
    assert part.counted is True
    assert part.progress == (1, 1)
    assert part.counted_entities == ['First Region']
    assert part.allocated_mandates == 1
    assert part.has_results is True
    assert part.results[0].accounted_ballots == 258
    assert part.results[0].accounted_votes == 216
    assert part.results[0].blank_ballots == 12
    assert part.results[0].counted == True
    assert part.results[0].domain_segment == 'First Region'
    assert part.results[0].domain_supersegment == 'First Superregion'
    assert part.results[0].eligible_voters == 400
    assert part.results[0].expats == 40
    assert part.results[0].invalid_ballots == 30
    assert part.results[0].received_ballots == 300
    assert part.results[0].turnout == 75.0
    assert part.totals.accounted_ballots == 258
    assert part.totals.accounted_votes == 216
    assert part.totals.blank_ballots == 12
    assert part.totals.eligible_voters == 400
    assert part.totals.expats == 40
    assert part.totals.invalid_ballots == 30
    assert part.totals.received_ballots == 300
    assert part.totals.turnout == 75.0

    # Add party results
    compound.party_results.append(
        PartyResult(
            domain='canton',
            domain_segment='',
            number_of_mandates=0,
            votes=10,
            total_votes=100,
            name_translations={'en_US': 'Libertarian'},
            party_id='1'
        )
    )
    party_result = PartyResult(
        domain='superregion',
        domain_segment='First Superregion',
        number_of_mandates=0,
        votes=0,
        total_votes=100,
        name_translations={'en_US': 'Libertarian'},
        party_id='1'
    )
    compound.party_results.append(party_result)
    compound.party_results.append(
        PartyResult(
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
    assert part.has_party_results is False
    party_result.votes = 10
    assert part.party_results[0].votes == 10
    # undo mypy narrowing
    part = part
    assert part.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = Decimal('10')
    assert part.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = Decimal('0')
    party_result.number_of_mandates = 1
    assert part.has_party_results is True

    # Clear results
    compound.clear_results()
    assert part.last_result_change is None
    assert part.party_results == []


def test_election_compound_part_historical_party_strengths(
    session: Session
) -> None:
    first_compound = ElectionCompound(
        title='First',
        domain='canton',
        date=date(2014, 1, 1),
        colors={'a': 'x'}
    )
    second_compound = ElectionCompound(
        title='Second',
        domain='canton',
        date=date(2018, 1, 1),
        colors={'a': 'y', 'b': 'y'}
    )
    third_compound = ElectionCompound(
        title='Third',
        domain='canton',
        date=date(2022, 1, 1),
        colors={'b': 'z', 'c': 'z'}
    )
    session.add(first_compound)
    session.add(second_compound)
    session.add(third_compound)
    session.flush()
    first = ElectionCompoundPart(first_compound, 'superregion', '1')
    second = ElectionCompoundPart(second_compound, 'superregion', '1')
    third = ElectionCompoundPart(third_compound, 'superregion', '1')

    assert first.historical_party_results == []
    assert second.historical_party_results == []
    assert third.historical_party_results == []
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y'}
    assert third.historical_colors == {'b': 'z', 'c': 'z'}

    # add results
    for (compound, year, party_id, domain, segment) in (
        (first_compound, 2014, 1, 'superregion', '1'),
        (first_compound, 2014, 2, 'superregion', '1'),
        (first_compound, 2014, 3, 'superregion', '1'),
        (first_compound, 2010, 1, 'superregion', '1'),
        (first_compound, 2010, 2, 'superregion', '2'),
        (first_compound, 2010, 3, 'canton', ''),
        (second_compound, 2022, 2, 'superregion', '1'),
        (second_compound, 2022, 3, 'superregion', '1'),
        (second_compound, 2018, 2, 'superregion', '1'),
        (second_compound, 2018, 3, 'superregion', '1'),
        (second_compound, 2018, 4, 'superregion', '1'),
        (second_compound, 2010, 2, 'superregion', '2'),
        (second_compound, 2010, 3, 'canton', ''),
        (third_compound, 2022, 1, 'superregion', '1'),
        (third_compound, 2022, 3, 'superregion', '1'),
        (third_compound, 2022, 5, 'superregion', '2'),
        (third_compound, 2022, 5, 'canton', ''),
    ):
        compound.party_results.append(
            PartyResult(
                year=year,
                number_of_mandates=0,
                votes=1,
                total_votes=100,
                name_translations={'en_US': str(party_id)},
                party_id=str(party_id),
                domain=domain,
                domain_segment=segment
            )
        )

    # no relationships yet
    assert len(first.historical_party_results) == 4
    assert len(second.historical_party_results) == 5
    assert len(third.historical_party_results) == 2
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y'}
    assert third.historical_colors == {'b': 'z', 'c': 'z'}

    # add relationships
    for (source_, target, type_) in (
        (third_compound, second_compound, 'historical'),
        (third_compound, first_compound, 'historical'),
        (second_compound, first_compound, 'historical'),
        (first_compound, second_compound, None),
        (second_compound, third_compound, 'historical')
    ):
        session.add(
            ElectionCompoundRelationship(
                source_id=source_.id, target_id=target.id, type=type_
            )
        )

    def extract(
        compound: ElectionCompoundPart
    ) -> list[tuple[str | None, int, str]]:
        return sorted(
            (result.election_compound_id, result.year, result.party_id)
            for result in compound.historical_party_results
        )

    assert extract(first) == [
        ('first', 2010, '1'),
        ('first', 2014, '1'),
        ('first', 2014, '2'),
        ('first', 2014, '3'),
    ]
    assert extract(second) == [
        ('first', 2014, '1'),
        ('first', 2014, '2'),
        ('first', 2014, '3'),
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
    ]
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y', 'c': 'z'}
    assert third.historical_colors == {'b': 'z', 'c': 'z', 'a': 'y'}
