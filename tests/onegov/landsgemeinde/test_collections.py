from __future__ import annotations

from datetime import date
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.collections import VotumCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_assembly_collections(session: Session) -> None:
    assemblies = AssemblyCollection(session)
    assert assemblies.query().count() == 0
    assert assemblies.by_id(None) is None  # type: ignore[arg-type]
    assert assemblies.by_date(None) is None  # type: ignore[arg-type]
    assert assemblies.by_date(date(2023, 5, 7)) is None

    assemblies.add(state='scheduled', date=date(2021, 5, 7))
    assemblies.add(state='scheduled', date=date(2023, 5, 7))
    assembly = assemblies.add(state='scheduled', date=date(2022, 5, 7))

    assert [x.date.year for x in assemblies.query()] == [2023, 2022, 2021]

    assert assemblies.by_date(date(2023, 5, 7)).date.year == 2023  # type: ignore[union-attr]
    assert assemblies.by_date(date(2021, 5, 7)).date.year == 2021  # type: ignore[union-attr]

    assert assemblies.by_id(assembly.id).date.year == 2022  # type: ignore[union-attr]


def test_agenda_item_collections(session: Session) -> None:
    assemblies = AssemblyCollection(session)
    assembly_1 = assemblies.add(state='scheduled', date=date(2021, 5, 7))
    assembly_2 = assemblies.add(state='scheduled', date=date(2022, 5, 7))

    items = AgendaItemCollection(session)
    assert items.query().count() == 0
    assert items.preloaded_by_assembly(assembly_1).count() == 0
    assert items.by_id(None) is None  # type: ignore[arg-type]
    assert items.by_number(None) is None  # type: ignore[arg-type]
    assert items.by_number(1) is None
    assert items.assembly is None

    items.add(state='scheduled', number=1, assembly_id=assembly_1.id)
    items.add(state='scheduled', number=3, assembly_id=assembly_2.id)
    items.add(state='scheduled', number=1, assembly_id=assembly_2.id)
    item = items.add(state='scheduled', number=2, assembly_id=assembly_2.id)

    items = AgendaItemCollection(session)
    items_0 = AgendaItemCollection(session, date(2020, 5, 7))
    items_1 = AgendaItemCollection(session, date(2021, 5, 7))
    items_2 = AgendaItemCollection(session, date(2022, 5, 7))
    items_3 = AgendaItemCollection(session, date(2023, 5, 7))

    assert items.query().count() == 4
    assert items_0.query().count() == 0
    assert items_1.query().count() == 1
    assert items_2.query().count() == 3
    assert items_3.query().count() == 0

    assert [x.number for x in items_2.query()] == [1, 2, 3]

    assert items.assembly is None
    assert items_0.assembly is None
    assert items_1.assembly is not None
    assert items_1.assembly.date.year == 2021
    assert items_2.assembly is not None
    assert items_2.assembly.date.year == 2022
    assert items_3.assembly is None

    assert items.by_id(item.id) == item
    assert items_0.by_id(item.id) == item
    assert items_1.by_id(item.id) == item
    assert items_2.by_id(item.id) == item
    assert items_3.by_id(item.id) == item

    assert items.by_number(1) is None
    assert items_0.by_number(1) is None
    assert items_1.by_number(1).date.year == 2021  # type: ignore[union-attr]
    assert items_2.by_number(1).date.year == 2022  # type: ignore[union-attr]
    assert items_3.by_number(1) is None

    assert items.preloaded_by_assembly(assembly_1).count() == 1
    assert items_0.preloaded_by_assembly(assembly_1).count() == 1
    assert items_1.preloaded_by_assembly(assembly_1).count() == 1
    assert items_2.preloaded_by_assembly(assembly_1).count() == 1
    assert items_3.preloaded_by_assembly(assembly_1).count() == 1
    assert items.preloaded_by_assembly(assembly_2).count() == 3
    assert items_0.preloaded_by_assembly(assembly_2).count() == 3
    assert items_1.preloaded_by_assembly(assembly_2).count() == 3
    assert items_2.preloaded_by_assembly(assembly_2).count() == 3
    assert items_3.preloaded_by_assembly(assembly_2).count() == 3
    assert items_3.preloaded_by_assembly(assembly_2).all()


def test_votum_collection(session: Session) -> None:
    assemblies = AssemblyCollection(session)
    assembly_1 = assemblies.add(state='scheduled', date=date(2021, 5, 7))
    assembly_2 = assemblies.add(state='scheduled', date=date(2022, 5, 7))

    items = AgendaItemCollection(session)
    item_1 = items.add(state='scheduled', number=1, assembly_id=assembly_1.id)
    item_2 = items.add(state='scheduled', number=2, assembly_id=assembly_2.id)

    vota = VotumCollection(session)
    assert vota.query().count() == 0
    assert vota.by_id(None) is None  # type: ignore[arg-type]
    assert vota.by_number(None) is None  # type: ignore[arg-type]
    assert vota.by_number(1) is None
    assert vota.assembly is None
    assert vota.agenda_item is None

    votum = vota.add(state='scheduled', number=1, agenda_item_id=item_1.id)
    votum_3 = vota.add(state='scheduled', number=3, agenda_item_id=item_2.id)
    votum_1 = vota.add(state='scheduled', number=1, agenda_item_id=item_2.id)
    votum_2 = vota.add(state='scheduled', number=2, agenda_item_id=item_2.id)

    vota = VotumCollection(session)
    vota_1 = VotumCollection(session, date(2021, 5, 7))
    vota_2 = VotumCollection(session, date(2022, 5, 7))
    vota_3 = VotumCollection(session, date(2023, 5, 7))
    vota_1_1 = VotumCollection(session, date(2021, 5, 7), 1)
    vota_1_2 = VotumCollection(session, date(2021, 5, 7), 2)
    vota_1_3 = VotumCollection(session, date(2021, 5, 7), 3)
    vota_2_1 = VotumCollection(session, date(2022, 5, 7), 1)
    vota_2_2 = VotumCollection(session, date(2022, 5, 7), 2)
    vota_2_3 = VotumCollection(session, date(2022, 5, 7), 3)
    vota_3_1 = VotumCollection(session, date(2023, 5, 7), 1)
    vota_3_2 = VotumCollection(session, date(2023, 5, 7), 2)
    vota_3_3 = VotumCollection(session, date(2023, 5, 7), 3)
    vota__1 = VotumCollection(session, agenda_item_number=1)
    vota__2 = VotumCollection(session, agenda_item_number=2)
    vota__3 = VotumCollection(session, agenda_item_number=3)

    assert vota.query().count() == 4
    assert vota_1.query().count() == 1
    assert vota_2.query().count() == 3
    assert vota_3.query().count() == 0
    assert vota_1_1.query().count() == 1
    assert vota_1_2.query().count() == 0
    assert vota_1_3.query().count() == 0
    assert vota_2_1.query().count() == 0
    assert vota_2_2.query().count() == 3
    assert vota_2_3.query().count() == 0
    assert vota_3_1.query().count() == 0
    assert vota_3_2.query().count() == 0
    assert vota_3_3.query().count() == 0
    assert vota__1.query().count() == 1
    assert vota__2.query().count() == 3
    assert vota__3.query().count() == 0

    assert [x.number for x in vota_2_2.query()] == [1, 2, 3]

    assert vota.assembly is None
    assert vota_1.assembly is not None
    assert vota_1.assembly.date.year == 2021
    assert vota_2.assembly is not None
    assert vota_2.assembly.date.year == 2022
    assert vota_3.assembly is None
    assert vota_1_1.assembly is not None
    assert vota_1_1.assembly.date.year == 2021
    assert vota_1_2.assembly is not None
    assert vota_1_2.assembly.date.year == 2021
    assert vota_1_3.assembly is not None
    assert vota_1_3.assembly.date.year == 2021
    assert vota_2_1.assembly is not None
    assert vota_2_1.assembly.date.year == 2022
    assert vota_2_2.assembly is not None
    assert vota_2_2.assembly.date.year == 2022
    assert vota_2_3.assembly is not None
    assert vota_2_3.assembly.date.year == 2022
    assert vota_3_1.assembly is None
    assert vota_3_2.assembly is None
    assert vota_3_3.assembly is None
    assert vota__1.assembly is None
    assert vota__2.assembly is None
    assert vota__3.assembly is None

    assert vota.agenda_item is None
    assert vota_1.agenda_item is None
    assert vota_2.agenda_item is None
    assert vota_3.agenda_item is None
    assert vota_1_1.agenda_item is not None
    assert vota_1_1.agenda_item.date.year == 2021
    assert vota_1_2.agenda_item is None
    assert vota_1_3.agenda_item is None
    assert vota_2_1.agenda_item is None
    assert vota_2_2.agenda_item is not None
    assert vota_2_2.agenda_item.date.year == 2022
    assert vota_2_3.agenda_item is None
    assert vota_3_1.agenda_item is None
    assert vota_3_2.agenda_item is None
    assert vota_3_3.agenda_item is None
    assert vota__1.agenda_item is None
    assert vota__2.agenda_item is None
    assert vota__3.agenda_item is None

    assert vota.by_id(votum.id) == votum
    assert vota_1.by_id(votum.id) == votum
    assert vota_2.by_id(votum.id) == votum
    assert vota_3.by_id(votum.id) == votum
    assert vota_1_1.by_id(votum.id) == votum
    assert vota_1_2.by_id(votum.id) == votum
    assert vota_1_3.by_id(votum.id) == votum
    assert vota_2_1.by_id(votum.id) == votum
    assert vota_2_2.by_id(votum.id) == votum
    assert vota_2_3.by_id(votum.id) == votum
    assert vota_3_1.by_id(votum.id) == votum
    assert vota_3_2.by_id(votum.id) == votum
    assert vota_3_3.by_id(votum.id) == votum
    assert vota__1.by_id(votum.id) == votum
    assert vota__2.by_id(votum.id) == votum
    assert vota__3.by_id(votum.id) == votum

    assert vota.by_number(1) is None
    assert vota.by_number(2) is None
    assert vota.by_number(3) is None
    assert vota_1.by_number(1) is None
    assert vota_1.by_number(2) is None
    assert vota_1.by_number(3) is None
    assert vota_2.by_number(1) is None
    assert vota_2.by_number(2) is None
    assert vota_2.by_number(3) is None
    assert vota_3.by_number(1) is None
    assert vota_3.by_number(2) is None
    assert vota_3.by_number(3) is None
    assert vota_1_1.by_number(1) == votum
    assert vota_1_1.by_number(2) is None
    assert vota_1_1.by_number(3) is None
    assert vota_1_2.by_number(1) is None
    assert vota_1_2.by_number(2) is None
    assert vota_1_2.by_number(3) is None
    assert vota_1_3.by_number(1) is None
    assert vota_1_3.by_number(2) is None
    assert vota_1_3.by_number(3) is None
    assert vota_2_1.by_number(1) is None
    assert vota_2_1.by_number(2) is None
    assert vota_2_1.by_number(3) is None
    assert vota_2_2.by_number(1) == votum_1
    assert vota_2_2.by_number(2) == votum_2
    assert vota_2_2.by_number(3) == votum_3
    assert vota_2_3.by_number(1) is None
    assert vota_2_3.by_number(2) is None
    assert vota_2_3.by_number(3) is None
    assert vota_3_1.by_number(1) is None
    assert vota_3_1.by_number(2) is None
    assert vota_3_1.by_number(3) is None
    assert vota_3_2.by_number(1) is None
    assert vota_3_2.by_number(2) is None
    assert vota_3_2.by_number(3) is None
    assert vota_3_3.by_number(1) is None
    assert vota_3_3.by_number(2) is None
    assert vota_3_3.by_number(3) is None
    assert vota__1.by_number(1) is None
    assert vota__1.by_number(2) is None
    assert vota__1.by_number(3) is None
    assert vota__2.by_number(1) is None
    assert vota__2.by_number(2) is None
    assert vota__2.by_number(3) is None
    assert vota__3.by_number(1) is None
    assert vota__3.by_number(2) is None
    assert vota__3.by_number(3) is None
