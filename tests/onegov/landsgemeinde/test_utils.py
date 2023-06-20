from datetime import date
from lxml import etree
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from onegov.landsgemeinde.utils import ensure_states
from onegov.landsgemeinde.utils import update_ticker
from unittest.mock import Mock


def test_update_ticker(landsgemeinde_app, assembly):

    class Request:
        app = landsgemeinde_app
        include = Mock()
        get_translate = Mock()
        translate = Mock(return_value='__translated__')
        is_manager = True
        url = 'http://localhost'

    request = Request()
    agenda_item = assembly.agenda_items[0]

    update_ticker(request, assembly)
    update_ticker(request, assembly, action='refresh')
    update_ticker(request, assembly, action='update')
    update_ticker(request, assembly, agenda_item)
    update_ticker(request, assembly, agenda_item, action='refresh')
    update_ticker(request, assembly, agenda_item, action='update')

    calls = [call.args[0] for call in request.app.send_websocket.mock_calls]
    assert len(calls) == 5
    assert calls[0] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[1] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[2] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[3] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[4]['event'] == 'update'
    assert calls[4]['assembly'] == '2023-05-07'
    assert '__translated__ 2' in calls[4]['content']
    etree.fromstring(calls[4]['content'])


def test_ensure_states():
    def create():
        result = Assembly(state='ongoing', date=date(2023, 5, 7))
        result.agenda_items.append(AgendaItem(state='completed', number=1))
        result.agenda_items.append(AgendaItem(state='ongoing', number=2))
        result.agenda_items.append(AgendaItem(state='scheduled', number=3))
        result.agenda_items.append(AgendaItem(state='scheduled', number=4))
        result.agenda_items[0].vota.append(Votum(state='completed', number=1))
        result.agenda_items[0].vota.append(Votum(state='completed', number=2))
        result.agenda_items[0].vota.append(Votum(state='completed', number=3))
        result.agenda_items[1].vota.append(Votum(state='completed', number=1))
        result.agenda_items[1].vota.append(Votum(state='ongoing', number=2))
        result.agenda_items[1].vota.append(Votum(state='scheduled', number=3))
        result.agenda_items[3].vota.append(Votum(state='scheduled', number=1))
        result.agenda_items[3].vota.append(Votum(state='scheduled', number=2))
        return result

    def get(assembly):
        result = {'': assembly.state}
        result.update({f'{a.number}': a.state for a in assembly.agenda_items})
        result.update({
            f'{a.number}.{v.number}': v.state
            for a in assembly.agenda_items for v in a.vota
        })
        return {k: result[k] for k in sorted(result)}

    # assembly scheduled
    assembly = create()
    assembly.state = 'scheduled'
    ensure_states(assembly)
    assert set(get(assembly).values()) == {'scheduled'}

    # assembly completed
    assembly = create()
    assembly.state = 'completed'
    ensure_states(assembly)
    assert set(get(assembly).values()) == {'completed'}

    # 1 ongoing
    assembly = create()
    assembly.agenda_items[0].state = 'ongoing'
    ensure_states(assembly.agenda_items[0])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'ongoing',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'scheduled',
        '2.1': 'scheduled',
        '2.2': 'scheduled',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 1 scheduled
    assembly = create()
    assembly.agenda_items[0].state = 'scheduled'
    ensure_states(assembly.agenda_items[0])
    assert get(assembly) == {
        '': 'scheduled',
        '1': 'scheduled',
        '1.1': 'scheduled',
        '1.2': 'scheduled',
        '1.3': 'scheduled',
        '2': 'scheduled',
        '2.1': 'scheduled',
        '2.2': 'scheduled',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 1.2 ongoing
    assembly = create()
    assembly.agenda_items[0].vota[1].state = 'ongoing'
    ensure_states(assembly.agenda_items[0].vota[1])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'ongoing',
        '1.1': 'completed',
        '1.2': 'ongoing',
        '1.3': 'scheduled',
        '2': 'scheduled',
        '2.1': 'scheduled',
        '2.2': 'scheduled',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 1.3 completed
    assembly = create()
    assembly.agenda_items[0].vota[2].state = 'completed'
    ensure_states(assembly.agenda_items[0].vota[2])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing',
        '2.1': 'completed',
        '2.2': 'ongoing',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 2 completed
    assembly = create()
    assembly.agenda_items[1].state = 'completed'
    ensure_states(assembly.agenda_items[1])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 2 scheduled
    assembly = create()
    assembly.agenda_items[1].state = 'scheduled'
    ensure_states(assembly.agenda_items[1])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'scheduled',
        '2.1': 'scheduled',
        '2.2': 'scheduled',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 2.2 completed
    assembly = create()
    assembly.agenda_items[1].vota[1].state = 'completed'
    ensure_states(assembly.agenda_items[1].vota[1])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 2.3 ongoing
    assembly = create()
    assembly.agenda_items[1].vota[2].state = 'ongoing'
    ensure_states(assembly.agenda_items[1].vota[2])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'ongoing',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 2.3 completed
    assembly = create()
    assembly.agenda_items[1].vota[2].state = 'completed'
    ensure_states(assembly.agenda_items[1].vota[2])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 3 ongoing
    assembly = create()
    assembly.agenda_items[2].state = 'ongoing'
    ensure_states(assembly.agenda_items[2])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'ongoing',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 4 completed
    assembly = create()
    assembly.agenda_items[3].state = 'completed'
    ensure_states(assembly.agenda_items[3])
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'completed',
        '4.1': 'completed',
        '4.2': 'completed'
    }

    # 4.1 ongoing
    assembly = create()
    assembly.agenda_items[3].vota[0].state = 'ongoing'
    ensure_states(assembly.agenda_items[3].vota[0])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'ongoing',
        '4.1': 'ongoing',
        '4.2': 'scheduled'
    }

    # 4.1 completed
    assembly = create()
    assembly.agenda_items[3].vota[0].state = 'completed'
    ensure_states(assembly.agenda_items[3].vota[0])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'ongoing',
        '4.1': 'completed',
        '4.2': 'scheduled'
    }

    # 4.2 completed
    assembly = create()
    assembly.agenda_items[3].vota[1].state = 'completed'
    ensure_states(assembly.agenda_items[3].vota[1])
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'completed',
        '4.1': 'completed',
        '4.2': 'completed'
    }

    # add 5 scheduled
    assembly = create()
    assembly.agenda_items.append(AgendaItem(state='scheduled', number=5))
    ensure_states(assembly.agenda_items[4])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing',
        '2.1': 'completed',
        '2.2': 'ongoing',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled',
        '5': 'scheduled'
    }

    # add 5 ongoing
    assembly = create()
    assembly.agenda_items.append(AgendaItem(state='ongoing', number=5))
    ensure_states(assembly.agenda_items[4])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'completed',
        '4.1': 'completed',
        '4.2': 'completed',
        '5': 'ongoing'
    }

    # add 5 completed
    assembly = create()
    assembly.agenda_items.append(AgendaItem(state='completed', number=5))
    ensure_states(assembly.agenda_items[4])
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'completed',
        '4.1': 'completed',
        '4.2': 'completed',
        '5': 'completed'
    }

    # add 4.3 ongoing
    assembly = create()
    assembly.agenda_items[3].vota.append(Votum(state='ongoing', number=3))
    ensure_states(assembly.agenda_items[3].vota[2])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'ongoing',
        '4.1': 'completed',
        '4.2': 'completed',
        '4.3': 'ongoing'
    }

    # add 4.3 completed
    assembly = create()
    assembly.agenda_items[3].vota.append(Votum(state='completed', number=3))
    ensure_states(assembly.agenda_items[3].vota[2])
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'completed',
        '4.1': 'completed',
        '4.2': 'completed',
        '4.3': 'completed'
    }

    # delete 4
    assembly = create()
    del assembly.agenda_items[3]
    ensure_states(assembly.agenda_items[2])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing',
        '2.1': 'completed',
        '2.2': 'ongoing',
        '2.3': 'scheduled',
        '3': 'scheduled',
    }

    # delete 4.2
    assembly = create()
    del assembly.agenda_items[3].vota[1]
    ensure_states(assembly.agenda_items[3].vota[0])
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing',
        '2.1': 'completed',
        '2.2': 'ongoing',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
    }