from __future__ import annotations

from onegov.landsgemeinde.layouts import DefaultLayout
from unittest.mock import Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.models import Assembly


def test_layouts(assembly: Assembly) -> None:

    class Request:
        include = Mock()
        app = Mock()
        is_manager = True
        locale = 'de_CH'

        def translate(self, text: str) -> str:
            return text

    layout = DefaultLayout(None, Request())  # type: ignore[arg-type]

    def a(x: Any) -> str:
        return layout.assembly_title(x).interpolate()  # type: ignore[attr-defined]

    def ai(*args: Any, **kwargs: Any) -> str:
        return layout.agenda_item_title(*args, **kwargs)

    assert a(assembly) == 'Assembly from 07. Mai 2023'
    assembly.extraordinary = True
    assert a(assembly) == 'Extraordinary Assembly from 07. Mai 2023'

    agenda_item = assembly.agenda_items[0]
    assert ai(agenda_item) == 'Agenda item 2'
    assert ai(agenda_item, short=True) == 'Agenda item 2'
    agenda_item.irrelevant = True
    assert ai(agenda_item) == 'Irrelevant motion'
    assert ai(agenda_item, short=True) == 'Irrelevant motion'
    agenda_item.title = 'title'
    assert ai(agenda_item) == 'title'
    assert ai(agenda_item, short=True) == 'title'
    agenda_item.irrelevant = False
    assert ai(agenda_item) == 'Agenda item 2: title'
    assert ai(agenda_item, short=True) == 'Agenda item 2'
    agenda_item.title = 'title\nA\nB'
    assert ai(agenda_item) == 'Agenda item 2: title\nA\nB'
    assert ai(agenda_item, short=True) == 'Agenda item 2'

    votum = agenda_item.vota[0]
    assert layout.votum_title(votum) == 'Votum 2'
