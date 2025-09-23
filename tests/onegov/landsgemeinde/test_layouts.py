from onegov.landsgemeinde.layouts import DefaultLayout
from unittest.mock import Mock


def test_layouts(assembly):

    class Request:
        include = Mock()
        app = Mock()
        is_manager = True
        locale = 'de_CH'

        def translate(self, text):
            return text

    layout = DefaultLayout(None, Request())

    def a(x):
        return layout.assembly_title(x).interpolate()

    def ai(*args, **kwargs):
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
