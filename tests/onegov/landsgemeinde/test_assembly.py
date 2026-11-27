from __future__ import annotations

from datetime import date
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.models import Assembly


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_assembly_fts_properties() -> None:
    assembly = Assembly(state='completed', date=date(2021, 5, 1))
    assert assembly.fts_public is True
    assert assembly.fts_suggestion == ('2021', 'Landsgemeinde 2021')
    assert assembly.fts_last_change is not None

    # a draft is not public
    assert Assembly(state='draft', date=date(2021, 5, 1)).fts_public is False


def test_assembly_collection(session: Session) -> None:
    assemblies = AssemblyCollection(session)
    assert assemblies.model_class is Assembly

    older = assemblies.add(state='completed', date=date(2020, 5, 1))
    newer = assemblies.add(state='completed', date=date(2021, 5, 1))
    session.flush()

    # ordered by date descending
    assert [a.date for a in assemblies.query()] == [newer.date, older.date]

    assert assemblies.by_id(newer.id) is newer
    assert assemblies.by_date(date(2020, 5, 1)) is older
    assert assemblies.by_date(date(1999, 1, 1)) is None
