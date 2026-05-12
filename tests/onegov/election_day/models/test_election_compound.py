from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal
from freezegun import freeze_time
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionCompoundRelationship
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from onegov.election_day.models import ListConnection
from onegov.election_day.models import ListPanachageResult
from onegov.election_day.models import ListResult
from onegov.election_day.models import PartyPanachageResult
from onegov.election_day.models import PartyResult
from onegov.election_day.models import ProporzElection
from pytz import UTC
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from io import BytesIO
    from onegov.election_day.types import DomainOfInfluence, Status
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def majorz_election() -> Election:
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
    election.title_translations['it_CH'] = 'Elezione'  # type: ignore[index]

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
        title: str = 'Proporz',
        id: str = 'proporz',
        shortcode: str = '1',
        domain: DomainOfInfluence = 'federation',
        date_: date | None = None,
        number_of_mandates: int = 1,
        absolute_majority: int = 144,
        status: Status | None = None,
        domain_supersegment: str = ''
) -> ProporzElection:
    date_ = date_ or date(2015, 6, 14)

    # election
    election = ProporzElection(
        title=title,
        id=id,
        shortcode=shortcode,
        domain=domain,
        date=date_,
        number_of_mandates=number_of_mandates,
        absolute_majority=absolute_majority,
        status=status,
        domain_supersegment=domain_supersegment
    )
    election.title_translations['it_CH'] = 'Elezione'  # type: ignore[index]

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
        ListPanachageResult(source_id=list_2.id, votes=12)
    )
    list_1.panachage_results.append(
        ListPanachageResult(source_id=None, votes=4)
    )

    return election


def test_election_compound_model(session: Session) -> None:
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
    assert election_compound.totals.turnout == 0
    assert election_compound.totals.eligible_voters == 0
    assert election_compound.totals.expats == 0
    assert election_compound.totals.received_ballots == 0
    assert election_compound.totals.accounted_ballots == 0
    assert election_compound.totals.blank_ballots == 0
    assert election_compound.totals.invalid_ballots == 0
    assert election_compound.totals.accounted_votes == 0
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

    election_compound.elections = list(session.query(Election).all())
    session.flush()
    # undo mypy narrowing
    election_compound = election_compound
    assert {election.id for election in election_compound.elections} == {
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
    assert election_compound.results[0].accounted_ballots == 0
    assert election_compound.results[0].accounted_votes == 0
    assert election_compound.results[0].blank_ballots == 0
    assert election_compound.results[0].counted == False
    assert election_compound.results[0].domain_segment == 'First district'
    assert election_compound.results[0].domain_supersegment == ''
    assert election_compound.results[0].eligible_voters == 0
    assert election_compound.results[0].expats == 0
    assert election_compound.results[0].invalid_ballots == 0
    assert election_compound.results[0].received_ballots == 0
    assert election_compound.results[0].turnout == 0
    assert election_compound.results[1].accounted_ballots == 0
    assert election_compound.results[1].accounted_votes == 0
    assert election_compound.results[1].blank_ballots == 0
    assert election_compound.results[1].counted == False
    assert election_compound.results[1].domain_segment == 'Second district'
    assert election_compound.results[1].domain_supersegment == ''
    assert election_compound.results[1].eligible_voters == 0
    assert election_compound.results[1].expats == 0
    assert election_compound.results[1].invalid_ballots == 0
    assert election_compound.results[1].received_ballots == 0
    assert election_compound.results[1].turnout == 0
    assert election_compound.totals.accounted_ballots == 0
    assert election_compound.totals.accounted_votes == 0
    assert election_compound.totals.blank_ballots == 0
    assert election_compound.totals.eligible_voters == 0
    assert election_compound.totals.expats == 0
    assert election_compound.totals.invalid_ballots == 0
    assert election_compound.totals.received_ballots == 0
    assert election_compound.totals.turnout == 0
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

    # undo mypy narrowing
    election_compound = election_compound
    assert election_compound.counted is False
    assert election_compound.progress == (0, 2)
    assert election_compound.counted_entities == []
    assert election_compound.allocated_mandates == 0
    assert election_compound.has_results is False
    assert election_compound.has_party_results is False
    assert election_compound.has_party_panachage_results is False
    assert election_compound.results[0].accounted_ballots == 258
    assert election_compound.results[0].accounted_votes == 216
    assert election_compound.results[0].blank_ballots == 12
    assert election_compound.results[0].counted == False
    assert election_compound.results[0].domain_segment == 'First district'
    assert election_compound.results[0].domain_supersegment == ''
    assert election_compound.results[0].eligible_voters == 400
    assert election_compound.results[0].expats == 40
    assert election_compound.results[0].invalid_ballots == 30
    assert election_compound.results[0].received_ballots == 300
    assert election_compound.results[0].turnout == 75.0
    assert election_compound.results[1].accounted_ballots == 258
    assert election_compound.results[1].accounted_votes == 474
    assert election_compound.results[1].blank_ballots == 12
    assert election_compound.results[1].counted == False
    assert election_compound.results[1].domain_segment == 'Second district'
    assert election_compound.results[1].domain_supersegment == ''
    assert election_compound.results[1].eligible_voters == 400
    assert election_compound.results[1].expats == 40
    assert election_compound.results[1].invalid_ballots == 30
    assert election_compound.results[1].received_ballots == 300
    assert election_compound.results[1].turnout == 75.0
    assert election_compound.totals.accounted_ballots == 0
    assert election_compound.totals.accounted_votes == 0
    assert election_compound.totals.blank_ballots == 0
    assert election_compound.totals.eligible_voters == 0
    assert election_compound.totals.expats == 0
    assert election_compound.totals.invalid_ballots == 0
    assert election_compound.totals.received_ballots == 0
    assert election_compound.totals.turnout == 0
    assert election_compound.completed is False

    # Set results as counted
    session.query(ElectionResult).first().counted = True  # type: ignore[union-attr]
    # undo mypy narrowing
    election_compound = election_compound
    assert election_compound.counted is False
    assert election_compound.progress == (0, 2)
    assert election_compound.counted_entities == []
    assert election_compound.allocated_mandates == 0
    assert election_compound.has_results == True
    assert election_compound.results[0].accounted_ballots == 258
    assert election_compound.results[0].accounted_votes == 216
    assert election_compound.results[0].blank_ballots == 12
    assert election_compound.results[0].counted == False
    assert election_compound.results[0].domain_segment == 'First district'
    assert election_compound.results[0].domain_supersegment == ''
    assert election_compound.results[0].eligible_voters == 400
    assert election_compound.results[0].expats == 40
    assert election_compound.results[0].invalid_ballots == 30
    assert election_compound.results[0].received_ballots == 300
    assert election_compound.results[0].turnout == 75.0
    assert election_compound.results[1].accounted_ballots == 258
    assert election_compound.results[1].accounted_votes == 474
    assert election_compound.results[1].blank_ballots == 12
    assert election_compound.results[1].counted == False
    assert election_compound.results[1].domain_segment == 'Second district'
    assert election_compound.results[1].domain_supersegment == ''
    assert election_compound.results[1].eligible_voters == 400
    assert election_compound.results[1].expats == 40
    assert election_compound.results[1].invalid_ballots == 30
    assert election_compound.results[1].received_ballots == 300
    assert election_compound.results[1].turnout == 75.0
    assert election_compound.totals.accounted_ballots == 0
    assert election_compound.totals.accounted_votes == 0
    assert election_compound.totals.blank_ballots == 0
    assert election_compound.totals.eligible_voters == 0
    assert election_compound.totals.expats == 0
    assert election_compound.totals.invalid_ballots == 0
    assert election_compound.totals.received_ballots == 0
    assert election_compound.totals.turnout == 0
    assert election_compound.completed is False

    for result in session.query(ElectionResult):
        result.counted = True
    # undo mypy narrowing
    election_compound = election_compound
    assert election_compound.counted is True
    assert election_compound.progress == (2, 2)
    assert election_compound.counted_entities == [
        'First district', 'Second district'
    ]
    assert election_compound.allocated_mandates == 0
    assert election_compound.completed == True
    assert election_compound.totals.accounted_ballots == 258 + 258
    assert election_compound.totals.accounted_votes == 216 + 474
    assert election_compound.totals.blank_ballots == 12 + 12
    assert election_compound.totals.eligible_voters == 400 + 400
    assert election_compound.totals.expats == 40 + 40
    assert election_compound.totals.invalid_ballots == 30 + 30
    assert election_compound.totals.received_ballots == 300 + 300
    assert election_compound.totals.turnout == 75.0

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
    election_compound.party_results = [party_result]
    assert election_compound.has_party_results is False
    party_result.votes = 10
    # undo mypy narrowing
    election_compound = election_compound
    assert election_compound.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = Decimal('10')
    assert election_compound.has_party_results is True
    party_result.votes = 0
    party_result.voters_count = Decimal('0')
    party_result.number_of_mandates = 1
    assert election_compound.has_party_results is True

    # Add panachage results
    panachage_result = PartyPanachageResult(
        election_compound_id=election_compound.id,
        source='A',
        target='B',
        votes=0,
    )
    election_compound.party_panachage_results = [panachage_result]
    assert election_compound.has_party_panachage_results is False

    # undo mypy narrowing
    election_compound = election_compound
    panachage_result.votes = 10
    assert election_compound.has_party_panachage_results is True

    election_compound.last_result_change = election_compound.timestamp()

    # Clear results
    election_compound.clear_results(True)
    # undo mypy narrowing
    election_compound = election_compound
    assert election_compound.last_result_change is None
    assert election_compound.party_results == []
    assert election_compound.party_panachage_results == []
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
    election_compound.party_results = [party_result]

    panachage_result = PartyPanachageResult(
        election_compound_id=election_compound.id,
        source='A',
        target='B',
        votes=0,
    )
    election_compound.party_panachage_results = [panachage_result]

    session.delete(election_compound)
    session.flush()

    assert session.query(PartyResult).first() is None
    assert session.query(PartyPanachageResult).first() is None


def test_election_compound_id_generation(session: Session) -> None:
    election_compound = ElectionCompound(
        title='Legislative Elections',
        domain='canton',
        date=date(2015, 6, 14),
    )
    session.add(election_compound)
    session.flush()
    assert election_compound.id == 'legislative-elections'

    election_compound = ElectionCompound(
        title='Legislative Elections',
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(election_compound)
    session.flush()
    assert election_compound.id == 'legislative-elections-1'

    election_compound = ElectionCompound(
        title='Legislative Elections',
        short_title='Leg. Els.',
        domain='federation',
        date=date(2015, 6, 14),
    )
    session.add(election_compound)
    session.flush()
    assert election_compound.id == 'leg-els'


def test_election_compound_last_modified(session: Session) -> None:
    with freeze_time("2001-01-01"):
        compound = ElectionCompound(
            title='Elections',
            domain='canton',
            date=date(2015, 6, 14),
        )
        assert compound.last_modified is None

        session.add(compound)
        session.flush()
        # undo mypy narrowing
        compound = compound
        assert compound.last_modified is not None
        assert compound.last_modified.isoformat().startswith('2001')
        assert session.query(ElectionCompound.last_modified
            ).scalar().isoformat().startswith('2001')

    with freeze_time("2002-01-01"):
        compound.last_result_change = compound.timestamp()
        session.flush()
        assert compound.last_modified.isoformat().startswith('2002')
        assert session.query(ElectionCompound.last_modified
            ).scalar().isoformat().startswith('2002')

    with freeze_time("2003-01-01"):
        compound.domain = 'federation'
        session.flush()
        assert compound.last_modified.isoformat().startswith('2003')
        assert session.query(ElectionCompound.last_modified
            ).scalar().isoformat().startswith('2003')


def test_related_election_compounds(session: Session) -> None:
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


def test_election_compound_rename(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO
) -> None:

    session = election_day_app_zg.session()

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
    election_compound.elections = list(session.query(Election).all())
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

    election_compound.explanations_pdf = (explanations_pdf, 'explanations.pdf')

    # Check IDs
    assert session.query(
        Election.election_compound_id
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
        Election.election_compound_id
    ).distinct().scalar() == 'y'
    assert len(election_compound.elections) == 2
    assert ('y',) in session.query(
        PartyResult.election_compound_id
    ).distinct().all()
    assert ('y',) in session.query(
        PartyPanachageResult.election_compound_id
    ).distinct().all()


def test_election_compound_manual_completion(session: Session) -> None:

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
        date_=date(2020, 3, 22),
        number_of_mandates=1,
        status='interim'
    )
    election_2 = proporz_election(
        title='Election 2',
        id='2',
        shortcode='P2',
        domain='region',
        date_=date(2020, 3, 22),
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

    election_compound.elections = [election_1, election_2]
    assert election_1.election_compound == election_compound
    assert election_2.election_compound == election_compound
    assert election_compound.completed is False
    assert election_compound.progress == (1, 2)
    assert election_1.completed is False
    assert election_2.completed is True

    # Manual completion, not completed
    election_compound.completes_manually = True
    # undo mypy narrowing
    election_2 = election_2
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
    # undo mypy narrowing
    election_2 = election_2
    assert election_compound.completed is False
    assert election_compound.progress == (1, 2)
    assert election_1.completed is False
    assert election_2.completed is True

    election_1.status = 'final'
    # undo mypy narrowing
    election_compound = election_compound
    election_1 = election_1
    assert election_compound.completed is True
    assert election_compound.progress == (2, 2)
    assert election_1.completed is True
    assert election_2.completed is True


def test_election_compound_supersegment_progress(session: Session) -> None:

    election_compound = ElectionCompound(
        title='Elections',
        id='elections',
        domain='canton',
        date=date(2020, 3, 22),
    )
    elections: list[Election] = [
        proporz_election(
            title='Election 1',
            id='1',
            shortcode='P1',
            domain='region',
            date_=date(2020, 3, 22),
            number_of_mandates=1,
            status='interim',
            domain_supersegment='A'
        ),
        proporz_election(
            title='Election 2',
            id='2',
            shortcode='P2',
            domain='region',
            date_=date(2020, 3, 22),
            number_of_mandates=1,
            status='final',
            domain_supersegment='A'
        ),
        proporz_election(
            title='Election 3',
            id='3',
            shortcode='P3',
            domain='region',
            date_=date(2020, 3, 22),
            number_of_mandates=1,
            status='final',
            domain_supersegment='B'
        ),
        proporz_election(
            title='Election 4',
            id='4',
            shortcode='P4',
            domain='region',
            date_=date(2020, 3, 22),
            number_of_mandates=1,
            status='interim',
            domain_supersegment=''
        )
    ]
    session.add_all([election_compound, *elections])
    session.flush()

    election_compound.elections = elections

    assert elections[0].completed is False
    assert elections[1].completed is True
    assert elections[2].completed is True
    assert elections[3].completed is False
    assert election_compound.completed is False
    assert election_compound.progress == (1, 3)


def test_election_compound_attachments(
    election_day_app_zg: TestApp,
    explanations_pdf: BytesIO,
    upper_apportionment_pdf: BytesIO,
    lower_apportionment_pdf: BytesIO
) -> None:

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

    # undo mypy narrowing
    model = model

    model.explanations_pdf = (explanations_pdf, 'e.pdf')
    file = model.explanations_pdf
    assert file is not None
    assert file.name == 'explanations_pdf'
    assert file.reference.filename == 'e.pdf'
    assert file.reference.content_type == 'application/pdf'

    model.upper_apportionment_pdf = (upper_apportionment_pdf, 'u.pdf')
    file = model.upper_apportionment_pdf
    assert file is not None
    assert file.name == 'upper_apportionment_pdf'
    assert file.reference.filename == 'u.pdf'
    assert file.reference.content_type == 'application/pdf'

    model.lower_apportionment_pdf = (lower_apportionment_pdf, 'l.pdf')
    file = model.lower_apportionment_pdf
    assert file is not None
    assert file.name == 'lower_apportionment_pdf'
    assert file.reference.filename == 'l.pdf'
    assert file.reference.content_type == 'application/pdf'

    del model.explanations_pdf
    del model.upper_apportionment_pdf
    del model.lower_apportionment_pdf

    assert model.explanations_pdf is None
    assert model.upper_apportionment_pdf is None
    assert model.lower_apportionment_pdf is None


def test_election_compound_historical_party_strengths(
    session: Session
) -> None:
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

    assert first.historical_party_results == []
    assert second.historical_party_results == []
    assert third.historical_party_results == []
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
    assert len(first.historical_party_results) == 6
    assert len(second.historical_party_results) == 7
    assert len(third.historical_party_results) == 4
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

    def extract(
        compound: ElectionCompound
    ) -> list[tuple[str | None, int, str]]:
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
    assert len([
        result for result in third.historical_party_results
        if result.domain == 'superregion'
    ]) == 1
    assert first.historical_colors == {'a': 'x'}
    assert second.historical_colors == {'a': 'y', 'b': 'y', 'c': 'z'}
    assert third.historical_colors == {'b': 'z', 'c': 'z', 'a': 'y'}
