from __future__ import annotations

from datetime import date
from onegov.landsgemeinde.models import AgendaItem, Assembly


def test_agenda_item_fts_public() -> None:
    assert AgendaItem(
        state='completed', number=1, title='A').fts_public is True
    assert AgendaItem(
        state='draft', number=1, title='A').fts_public is False


def test_agenda_item_fts_suggestion() -> None:
    item = AgendaItem(
        state='completed', number=1,
        title='A. Budget\nxx\nB. Rechnung')
    # each line yields itself, and a variant without the A./B. prefix;
    # lines shorter than three characters are skipped
    assert item.fts_suggestion == [
        'A. Budget', 'Budget', 'B. Rechnung', 'Rechnung']


def test_agenda_item_fts_last_change() -> None:
    item = AgendaItem(state='completed', number=1, title='A')
    assembly = Assembly(state='completed', date=date(2021, 5, 1))
    item.assembly = assembly
    # transient item -> _fetch_if_necessary returns early, uses the assembly
    assert item.fts_last_change == assembly.fts_last_change
