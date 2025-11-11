from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionRelationship
from onegov.election_day.models import ElectionResult
from pytest import mark
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from io import BytesIO
    from onegov.election_day.types import Status
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def majorz_election() -> Election:
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
    election.last_result_change = election.timestamp()
    return election


def test_election_create_all_models(session: Session) -> None:
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

    assert election.candidates == [candidate]
    assert election.results == [election_result]

    assert candidate.results == [candidate_result]
    assert candidate.election == election

    assert election_result.candidate_results == [candidate_result]
    assert election_result.election == election

    assert candidate_result.election_result == election_result
    assert candidate_result.candidate == candidate

    session.delete(election)
    session.flush()

    assert session.query(Candidate).all() == []
    assert session.query(CandidateResult).all() == []
    assert session.query(Election).all() == []
    assert session.query(ElectionResult).all() == []


def test_election_id_generation(session: Session) -> None:
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

    election = Election(
        title='Legislative Election',
        short_title='Leg. El.',
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(election)
    session.flush()
    assert election.id == 'leg-el'


def test_election_hybrid_properties(session: Session) -> None:
    # Election
    election = Election(
        title="Election",
        domain='federation',
        date=date(2015, 6, 14),
        number_of_mandates=2
    )

    session.add(election)
    session.flush()

    assert election.eligible_voters == 0
    assert election.expats == 0
    assert election.received_ballots == 0
    assert election.accounted_ballots == 0
    assert election.blank_ballots == 0
    assert election.invalid_ballots == 0
    assert election.accounted_votes == 0
    assert election.counted is False
    assert election.last_modified is not None
    assert election.unaccounted_ballots == 0
    assert election.accounted_ballots == 0
    assert election.turnout == 0

    assert session.query(Election.eligible_voters).scalar() == 0
    assert session.query(Election.expats).scalar() == 0
    assert session.query(Election.received_ballots).scalar() == 0
    assert session.query(Election.accounted_ballots).scalar() == 0
    assert session.query(Election.blank_ballots).scalar() == 0
    assert session.query(Election.invalid_ballots).scalar() == 0
    assert session.query(Election.accounted_votes).scalar() == 0
    assert session.query(Election.counted).scalar() is False
    assert session.query(Election.last_modified).scalar().date()
    assert session.query(Election.unaccounted_ballots).scalar() == 0
    assert session.query(Election.accounted_ballots).scalar() == 0
    assert session.query(Election.turnout).scalar() == 0

    for x in range(1, 4):
        election.results.append(
            ElectionResult(
                name='name',
                entity_id=x,
                counted=True,
                eligible_voters=100 * x,
                expats=10 * x,
                received_ballots=80 * x,
                blank_ballots=4 * x,
                invalid_ballots=3 * x,
                blank_votes=2 * x,
                invalid_votes=x
            )
        )
    session.flush()

    # undo mypy narrowing
    election = election
    assert election.eligible_voters == 600
    assert election.expats == 60
    assert election.received_ballots == 480
    assert election.accounted_ballots == 438
    assert election.blank_ballots == 24
    assert election.invalid_ballots == 18
    assert election.accounted_votes == 858
    assert election.counted is True
    assert election.last_modified is not None
    assert election.unaccounted_ballots == 42
    assert election.accounted_ballots == 438
    assert election.turnout == 80.0

    assert session.query(Election.eligible_voters).scalar() == 600
    assert session.query(Election.expats).scalar() == 60
    assert session.query(Election.received_ballots).scalar() == 480
    assert session.query(Election.accounted_ballots).scalar() == 438
    assert session.query(Election.blank_ballots).scalar() == 24
    assert session.query(Election.invalid_ballots).scalar() == 18
    assert session.query(Election.accounted_votes).scalar() == 858
    assert session.query(Election.counted).scalar() is True
    assert session.query(Election.last_modified).scalar().date()
    assert session.query(Election.unaccounted_ballots).scalar() == 42
    assert session.query(Election.accounted_ballots).scalar() == 438
    assert session.query(Election.turnout).scalar() == 80.0

    # Election Result
    election_result = next(r for r in election.results if r.entity_id == 1)
    assert election_result.unaccounted_ballots == 7
    assert election_result.accounted_ballots == 73
    assert election_result.turnout == 80.0
    assert election_result.accounted_votes == 143

    assert session.query(ElectionResult.unaccounted_ballots).filter_by(
        entity_id=1).scalar() == 7
    assert session.query(ElectionResult.accounted_ballots).filter_by(
        entity_id=1).scalar() == 73
    assert session.query(ElectionResult.turnout).filter_by(
        entity_id=1).scalar() == 80.0
    assert session.query(ElectionResult.accounted_votes).filter_by(
        entity_id=1).scalar() == 143

    election_result.eligible_voters = 0
    session.flush()
    election_result = next(r for r in election.results if r.entity_id == 1)
    assert election_result.turnout == 0
    assert session.query(ElectionResult.turnout).filter_by(
        entity_id=1).scalar() == 0


def test_election_counted(session: Session) -> None:
    election = Election(
        title='Legislative Election',
        domain='federation',
        date=date(2015, 6, 14),
    )

    session.add(election)
    session.flush()

    assert election.counted is False
    assert election.progress == (0, 0)
    assert election.counted_entities == []

    election.results.append(ElectionResult(
        name='A',
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
    assert election.counted_entities == []

    election.results.append(ElectionResult(
        name='B',
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
    assert election.counted_entities == ['B']

    for result in election.results:
        result.counted = True

    # undo mypy narrowing
    election = election
    assert election.counted is True
    assert election.progress == (2, 2)
    assert election.counted_entities == ['A', 'B']


def test_election_last_modified(session: Session) -> None:
    with freeze_time("2001-01-01"):
        election = Election(
            title='Legislative Election',
            domain='federation',
            date=date(2015, 6, 14),
        )
        assert election.last_modified is None

        session.add(election)
        session.flush()
        # undo mypy narrrowing
        election = election
        assert election.last_modified is not None
        assert election.last_modified.isoformat().startswith('2001')
        assert session.query(
            Election.last_modified
        ).scalar().isoformat().startswith('2001')

    with freeze_time("2002-01-01"):
        election.last_result_change = election.timestamp()
        session.flush()
        assert election.last_modified.isoformat().startswith('2002')
        assert session.query(
            Election.last_modified
        ).scalar().isoformat().startswith('2002')

    with freeze_time("2003-01-01"):
        election.domain = 'canton'
        session.flush()
        assert election.last_modified.isoformat().startswith('2003')
        assert session.query(
            Election.last_modified
        ).scalar().isoformat().startswith('2003')


def test_election_results(session: Session) -> None:
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

    assert sorted(c.votes for c in election.candidates) == []

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

    assert election.votes_by_district.all() == [  # type: ignore[comparison-overlap]
        ('election', None, [1, 2], True, 534)
    ]


def test_election_meta_data(session: Session) -> None:
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


def test_election_status(session: Session) -> None:
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

    # Test completed calculation
    # ... empty election
    status: Status | None
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


@mark.parametrize('clear_all', [True, False])
def test_election_clear(clear_all: bool, session: Session) -> None:
    election = majorz_election()
    session.add(election)
    session.flush()

    assert election.last_result_change
    assert election.absolute_majority
    assert election.status
    assert election.candidates
    assert election.results

    assert session.query(Candidate).first()
    assert session.query(CandidateResult).first()
    assert session.query(ElectionResult).first()

    election.clear_results(clear_all)

    # undo mypy narrowing
    election = election
    assert election.last_result_change is None
    assert election.absolute_majority is None
    assert election.status is None
    assert election.results == []

    assert session.query(CandidateResult).first() is None
    assert session.query(ElectionResult).first() is None

    if clear_all:
        assert len(election.candidates) == 0
        assert session.query(Candidate).first() is None
    else:
        assert len(election.candidates) > 0
        assert session.query(Candidate).first()


def test_election_has_results(session: Session) -> None:
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

    election.results[0].counted = True

    assert election.has_results is True


def test_related_elections(session: Session) -> None:
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

    first.related_elections.append(ElectionRelationship(target_id=second.id))
    session.flush()
    assert first.related_elections.one().source_id == 'first'
    assert first.related_elections.one().target_id == 'second'
    assert first.referencing_elections.all() == []
    assert second.related_elections.all() == []
    assert second.referencing_elections.one().source_id == 'first'
    assert second.referencing_elections.one().target_id == 'second'

    second.related_elections.append(ElectionRelationship(target_id=first.id))
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
    assert session.query(ElectionRelationship).all() == []

    first.related_elections.append(ElectionRelationship(target_id=first.id))
    session.flush()
    assert first.related_elections.one().source_id == 'first'
    assert first.related_elections.one().target_id == 'first'
    assert first.referencing_elections.one().source_id == 'first'
    assert first.referencing_elections.one().target_id == 'first'

    session.delete(first)
    session.flush()
    assert session.query(ElectionRelationship).all() == []


def test_election_rename(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO
) -> None:

    session = election_day_app_zg.session()

    election = majorz_election()
    session.add(election)
    session.flush()

    election.explanations_pdf = (explanations_pdf, 'explanations.pdf')

    assert session.query(Candidate).one().election_id == 'election'
    assert session.query(ElectionResult).one().election_id == 'election'

    election.id = 'elerction'
    session.flush()

    assert session.query(Candidate).one().election_id == 'elerction'
    assert session.query(ElectionResult).one().election_id == 'elerction'


def test_election_attachments(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO
) -> None:

    model = Election(
        title='Election',
        domain='canton',
        date=date(2017, 1, 1),
    )

    assert model.explanations_pdf is None
    del model.explanations_pdf
    model.explanations_pdf = (explanations_pdf, 'explanations.pdf')
    # undo my narrowing
    model = model
    assert model.explanations_pdf is not None
    assert model.explanations_pdf.name == 'explanations_pdf'
    assert model.explanations_pdf.reference.filename == 'explanations.pdf'
    assert model.explanations_pdf.reference.content_type == 'application/pdf'
    del model.explanations_pdf
    assert model.explanations_pdf is None
