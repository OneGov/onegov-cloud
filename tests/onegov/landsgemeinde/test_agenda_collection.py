from __future__ import annotations

from datetime import date
from onegov.landsgemeinde.collections import (
    AgendaItemCollection,
    AssemblyCollection,
)
from onegov.landsgemeinde.models import AgendaItem


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_agenda_item_collection(session: Session) -> None:
    assembly = AssemblyCollection(session).add(
        state='completed', date=date(2021, 5, 1))
    session.flush()

    items = AgendaItemCollection(session, date=date(2021, 5, 1))
    assert items.model_class is AgendaItem

    second = items.add(number=2, state='completed', assembly_id=assembly.id)
    first = items.add(number=1, state='completed', assembly_id=assembly.id)
    session.flush()

    # ordered by number ascending
    assert [i.number for i in items.query()] == [1, 2]

    assert items.by_id(first.id) is first
    assert items.by_number(1) is first
    assert items.assembly is assembly

    # preloaded query returns both items
    assert items.preloaded_by_assembly(assembly).count() == 2

    # without a date there is no assembly and by_number returns None
    undated = AgendaItemCollection(session)
    assert undated.assembly is None
    assert undated.by_number(1) is None
    assert second.number == 2
