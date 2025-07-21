from datetime import date
from onegov.pas.models import (
    Attendence,
    PASParliamentarian,
    PASParliamentarianRole,
    Party,
)
from onegov.pas.utils import get_parties_with_settlements
from onegov.pas.utils import get_parliamentarians_with_settlements
from uuid import uuid4


def test_get_parliamentarians_with_settlements(session):
    # Create test data
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)

    # Create parliamentarians
    parl1 = PASParliamentarian(
        id=uuid4(),
        first_name='John',
        last_name='Smith',
        gender='male',
    )

    parl2 = PASParliamentarian(
        id=uuid4(),
        first_name='Jane',
        last_name='Doe',
        gender='female',
    )

    parl3 = PASParliamentarian(
        id=uuid4(),
        first_name='Bob',
        last_name='Johnson',
        gender='male',
    )

    session.add_all([parl1, parl2, parl3])
    session.flush()

    # Create roles for each parliamentarian
    role1 = PASParliamentarianRole(
        parliamentarian_id=parl1.id,
        start=date(2023, 1, 1),
        end=date(2025, 12, 31),
        role='member',
        party_role='member',
        parliamentary_group_role='member',
    )

    role2 = PASParliamentarianRole(
        parliamentarian_id=parl2.id,
        start=date(2023, 1, 1),
        end=date(2025, 12, 31),
        role='member',
        party_role='member',
        parliamentary_group_role='member',
    )

    # PASParl3 has no active role during this period
    role3 = PASParliamentarianRole(
        parliamentarian_id=parl3.id,
        start=date(2020, 1, 1),
        end=date(2023, 12, 31),
        role='member',
        party_role='member',
        parliamentary_group_role='member',
    )

    session.add_all([role1, role2, role3])
    session.flush()

    # Create attendances
    attendance1 = Attendence(
        id=uuid4(),
        parliamentarian_id=parl1.id,
        date=date(2024, 6, 1),
        duration=60,
        type='plenary',
    )

    # Parl2 has no attendances

    # Parl3 has attendance but the role does not fall within the date range
    # of the attendance
    attendance3 = Attendence(
        id=uuid4(),
        parliamentarian_id=parl3.id,
        date=date(2024, 6, 1),
        duration=60,
        type='plenary',
    )

    session.add_all([attendance1, attendance3])
    session.flush()

    # Test the function
    result = get_parliamentarians_with_settlements(
        session, start_date, end_date
    )

    # Should only return parl1 who has both an active role and attendance
    assert len(result) == 1
    assert result[0].id == parl1.id

    # Add attendance for parl2 and test again
    attendance2 = Attendence(
        id=uuid4(),
        parliamentarian_id=parl2.id,
        date=date(2024, 6, 1),
        duration=60,
        type='plenary',
    )
    session.add(attendance2)
    session.flush()

    result = get_parliamentarians_with_settlements(
        session, start_date, end_date
    )

    # Now should return both parl1 and parl2
    assert len(result) == 2
    assert {p.id for p in result} == {parl1.id, parl2.id}

    # Test with different date range
    result = get_parliamentarians_with_settlements(
        session, date(2023, 1, 1), date(2023, 12, 31)
    )

    # Should return none as no attendances in this period
    assert len(result) == 0


def test_get_parties_with_settlements(session):
    # Create test data
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)

    # Create parties
    party_a = Party(
        id=uuid4(),
        name='Party A',
        start=date(2020, 1, 1),
        end=date(2026, 12, 31),
    )
    party_b = Party(
        id=uuid4(),
        name='Party B',
        start=date(2020, 1, 1),
        end=date(2026, 12, 31),
    )
    party_c = Party(
        id=uuid4(),
        name='Party C',
        start=date(2020, 1, 1),
        end=date(2026, 12, 31),
    )

    session.add_all([party_a, party_b, party_c])
    session.flush()

    # Create parliamentarians
    parl1 = PASParliamentarian(
        id=uuid4(),
        first_name='John',
        last_name='Smith',
        gender='male',
        shipping_method='a',
    )

    parl2 = PASParliamentarian(
        id=uuid4(),
        first_name='Jane',
        last_name='Doe',
        gender='female',
        shipping_method='a',
    )

    parl3 = PASParliamentarian(
        id=uuid4(),
        first_name='Bob',
        last_name='Johnson',
        gender='male',
        shipping_method='a',
    )

    session.add_all([parl1, parl2, parl3])
    session.flush()

    # Create roles
    # PASParl1 in Party A during the entire period
    role1 = PASParliamentarianRole(
        parliamentarian_id=parl1.id,
        party_id=party_a.id,
        start=date(2023, 1, 1),
        end=date(2025, 12, 31),
        role='member',
        party_role='member',
        parliamentary_group_role='member',
    )

    # PASParl2 switches from Party B to Party C in the middle of the period
    role2a = PASParliamentarianRole(
        parliamentarian_id=parl2.id,
        party_id=party_b.id,
        start=date(2023, 1, 1),
        end=date(2024, 6, 30),  # First half of 2024
        role='member',
        party_role='member',
        parliamentary_group_role='member',
    )

    role2b = PASParliamentarianRole(
        parliamentarian_id=parl2.id,
        party_id=party_c.id,
        start=date(2024, 7, 1),  # Second half of 2024
        end=date(2025, 12, 31),
        role='member',
        party_role='member',
        parliamentary_group_role='member',
    )

    # PASParl3 was in Party C but left before the period
    role3 = PASParliamentarianRole(
        parliamentarian_id=parl3.id,
        party_id=party_c.id,
        start=date(2020, 1, 1),
        end=date(2023, 12, 31),
        role='member',
        party_role='member',
        parliamentary_group_role='member',
    )

    session.add_all([role1, role2a, role2b, role3])
    session.flush()

    # Create attendances
    # PASParl1 has attendance during their party membership - one in first
    # half, one in second half
    attendance1a = Attendence(
        id=uuid4(),
        parliamentarian_id=parl1.id,
        date=date(2024, 3, 15),  # During party A membership
        # - first half
        duration=60,
        type='plenary',
    )

    attendance1b = Attendence(
        id=uuid4(),
        parliamentarian_id=parl1.id,
        date=date(2024, 9, 15),
        # During party A membership - second half
        duration=60,
        type='plenary',
    )

    # Parl2 has attendances during both party memberships
    attendance2a = Attendence(
        id=uuid4(),
        parliamentarian_id=parl2.id,
        date=date(2024, 3, 15),  # During party B membership
        duration=60,
        type='plenary',
    )

    attendance2b = Attendence(
        id=uuid4(),
        parliamentarian_id=parl2.id,
        date=date(2024, 9, 15),  # During party C membership
        type='plenary',
        duration=60,
    )

    # Parl3 has attendance but was no longer in Party C
    attendance3 = Attendence(
        id=uuid4(),
        parliamentarian_id=parl3.id,
        date=date(2024, 3, 15),
        duration=60,
        type='plenary',
    )

    session.add_all(
        [
            attendance1a,
            attendance1b,
            attendance2a,
            attendance2b,
            attendance3,
        ]
    )
    session.flush()

    # Test the function for the whole period
    result = get_parties_with_settlements(session, start_date, end_date)

    # Should return parties A, B, and C (not checking party C for parl3 since
    # their role ended)
    assert len(result) == 3
    party_ids = {p.id for p in result}
    assert party_a.id in party_ids
    assert party_b.id in party_ids
    assert party_c.id in party_ids

    # Test with first half of 2024
    first_half_result = get_parties_with_settlements(
        session, date(2024, 1, 1), date(2024, 6, 30)
    )

    # Should return only parties A and B
    assert len(first_half_result) == 2
    first_half_party_ids = {p.id for p in first_half_result}
    assert party_a.id in first_half_party_ids
    assert party_b.id in first_half_party_ids
    assert party_c.id not in first_half_party_ids

    # Test with second half of 2024
    second_half_result = get_parties_with_settlements(
        session, date(2024, 7, 1), date(2024, 12, 31)
    )

    # Should return only parties A and C
    assert len(second_half_result) == 2
    second_half_party_ids = {p.id for p in second_half_result}
    assert party_a.id in second_half_party_ids
    assert party_b.id not in second_half_party_ids
    assert party_c.id in second_half_party_ids

    # Test with period outside our data
    no_result = get_parties_with_settlements(
        session, date(2022, 1, 1), date(2022, 12, 31)
    )

    # Should return no parties
    assert len(no_result) == 0
