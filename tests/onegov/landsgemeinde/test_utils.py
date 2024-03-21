from datetime import date
from lxml import etree
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from onegov.landsgemeinde.utils import ensure_states
from onegov.landsgemeinde.utils import update_ticker
from freezegun import freeze_time


def test_update_ticker(landsgemeinde_app, assembly):

    class Request:
        app = landsgemeinde_app
        is_manager = True
        url = 'http://localhost'
        locale = 'de_CH'

        def include(self, asset):
            pass

        def translate(*args, **kwargs):
            return '__translated__'

        def get_translate(self, for_chameleon=False):
            return self.translate

    request = Request()
    agenda_item_2 = assembly.agenda_items[0]
    agenda_item_1 = assembly.agenda_items[1]
    votum_1_1 = agenda_item_1.vota[0]
    votum_2_1 = agenda_item_2.vota[0]

    update_ticker(request, {assembly})
    update_ticker(request, {assembly, agenda_item_1})
    update_ticker(request, {assembly, agenda_item_1, agenda_item_2})
    update_ticker(request, {assembly, agenda_item_1, votum_1_1})
    update_ticker(request, {assembly, agenda_item_1, votum_2_1})
    update_ticker(request, {agenda_item_1})
    update_ticker(request, {agenda_item_1, agenda_item_2})
    update_ticker(request, {agenda_item_1, votum_1_1})
    update_ticker(request, {agenda_item_1, votum_2_1})
    update_ticker(request, {votum_1_1, votum_2_1})

    calls = [call.args[0] for call in request.app.send_websocket.mock_calls]
    assert len(calls) == 13
    assert calls[0] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[1] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[2] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[3] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[4] == {'event': 'refresh', 'assembly': '2023-05-07'}
    assert calls[5]['event'] == 'update'
    assert calls[5]['assembly'] == '2023-05-07'
    assert calls[5]['node'] == 'agenda-item-1'
    assert '__translated__ 1' in calls[5]['content']
    etree.fromstring(calls[5]['content'])
    assert {call['event'] for call in calls[5:]} == {'update'}
    assert sorted([call['node'] for call in calls[5:]]) == [
        'agenda-item-1', 'agenda-item-1', 'agenda-item-1', 'agenda-item-1',
        'agenda-item-1', 'agenda-item-2', 'agenda-item-2', 'agenda-item-2'
    ]


@freeze_time("2024-05-05 10:00")
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
        result.agenda_items[1].start()
        return result

    def get(assembly):
        result = {'': assembly.state}
        result.update({
            f'{a.number}': f'{a.state} {a.start_time or ""}'.strip()
            for a in assembly.agenda_items
        })
        result.update({
            f'{a.number}.{v.number}': v.state
            for a in assembly.agenda_items for v in a.vota
        })
        return {k: result[k] for k in sorted(result)}

    # initial state
    assembly = create()
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing 12:00:00',
        '2.1': 'completed',
        '2.2': 'ongoing',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # assembly scheduled
    assembly = create()
    assembly.state = 'scheduled'
    assert ensure_states(assembly) == {
        assembly.agenda_items[0],  # was completed
        assembly.agenda_items[0].vota[0],  # was completed
        assembly.agenda_items[0].vota[1],  # was completed
        assembly.agenda_items[0].vota[2],  # was completed
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[0],  # was completed
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
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

    # assembly completed
    assembly = create()
    assembly.state = 'completed'
    assert ensure_states(assembly) == {
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
        assembly.agenda_items[3].vota[1],  # was scheduled
    }
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'completed',
        '4.1': 'completed',
        '4.2': 'completed'
    }

    # 1 ongoing
    assembly = create()
    assembly.agenda_items[0].state = 'ongoing'
    assert ensure_states(assembly.agenda_items[0]) == {
        assembly.agenda_items[0],  # start set
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[0],  # was completed
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'ongoing 12:00:00',
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
    assert ensure_states(assembly.agenda_items[0]) == {
        assembly.agenda_items[0].vota[0],  # was completed
        assembly.agenda_items[0].vota[1],  # was completed
        assembly.agenda_items[0].vota[2],  # was completed
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[0],  # was completed
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
    assert get(assembly) == {
        '': 'ongoing',
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
    assert ensure_states(assembly.agenda_items[0].vota[1]) == {
        assembly.agenda_items[0],  # was completed
        assembly.agenda_items[0].vota[2],  # was completed
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[0],  # was completed
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'ongoing 12:00:00',
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
    assert ensure_states(assembly.agenda_items[0].vota[2]) == set()
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing 12:00:00',
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
    assert ensure_states(assembly.agenda_items[1]) == {
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
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
    assert ensure_states(assembly.agenda_items[1]) == {
        assembly.agenda_items[1],  # start cleared
        assembly.agenda_items[1].vota[0],  # was completed
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
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
    assert ensure_states(assembly.agenda_items[1].vota[1]) == set()
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing 12:00:00',
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
    assert ensure_states(assembly.agenda_items[1].vota[2]) == {
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing 12:00:00',
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
    assert ensure_states(assembly.agenda_items[1].vota[2]) == {
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
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
    assert ensure_states(assembly.agenda_items[2]) == {
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # start set
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'ongoing 12:00:00',
        '4': 'scheduled',
        '4.1': 'scheduled',
        '4.2': 'scheduled'
    }

    # 4 completed
    assembly = create()
    assembly.agenda_items[3].state = 'completed'
    assert ensure_states(assembly.agenda_items[3]) == {
        assembly,  # was ongoing
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
        assembly.agenda_items[3].vota[1],  # was scheduled
    }
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
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
    assert ensure_states(assembly.agenda_items[3].vota[0]) == {
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled, start set
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'ongoing 12:00:00',
        '4.1': 'ongoing',
        '4.2': 'scheduled'
    }

    # 4.1 completed
    assembly = create()
    assembly.agenda_items[3].vota[0].state = 'completed'
    assert ensure_states(assembly.agenda_items[3].vota[0]) == {
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled, start set
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'ongoing 12:00:00',
        '4.1': 'completed',
        '4.2': 'scheduled'
    }

    # 4.2 completed
    assembly = create()
    assembly.agenda_items[3].vota[1].state = 'completed'
    assert ensure_states(assembly.agenda_items[3].vota[1]) == {
        assembly,  # was ongoing
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
    }
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
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
    assert ensure_states(assembly.agenda_items[4]) == set()
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing 12:00:00',
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
    assert ensure_states(assembly.agenda_items[4]) == {
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
        assembly.agenda_items[3].vota[1],  # was scheduled
        assembly.agenda_items[4]  # start set
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'completed',
        '4.1': 'completed',
        '4.2': 'completed',
        '5': 'ongoing 12:00:00'
    }

    # add 5 completed
    assembly = create()
    assembly.agenda_items.append(AgendaItem(state='completed', number=5))
    assert ensure_states(assembly.agenda_items[4]) == {
        assembly,  # was ongoing
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
        assembly.agenda_items[3].vota[1],  # was scheduled
    }
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
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
    assert ensure_states(assembly.agenda_items[3].vota[2]) == {
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
        assembly.agenda_items[3].vota[1],  # was scheduled
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
        '2.1': 'completed',
        '2.2': 'completed',
        '2.3': 'completed',
        '3': 'completed',
        '4': 'ongoing 12:00:00',
        '4.1': 'completed',
        '4.2': 'completed',
        '4.3': 'ongoing'
    }

    # add 4.3 completed
    assembly = create()
    assembly.agenda_items[3].vota.append(Votum(state='completed', number=3))
    assert ensure_states(assembly.agenda_items[3].vota[2]) == {
        assembly,  # was ongoing
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was scheduled
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
        assembly.agenda_items[3].vota[1],  # was scheduled
    }
    assert get(assembly) == {
        '': 'completed',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'completed 12:00:00',
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
    assert ensure_states(assembly.agenda_items[2]) == set()
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing 12:00:00',
        '2.1': 'completed',
        '2.2': 'ongoing',
        '2.3': 'scheduled',
        '3': 'scheduled',
    }

    # delete 4.2
    assembly = create()
    del assembly.agenda_items[3].vota[1]
    assert ensure_states(assembly.agenda_items[3].vota[0]) == set()
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'completed',
        '1.1': 'completed',
        '1.2': 'completed',
        '1.3': 'completed',
        '2': 'ongoing 12:00:00',
        '2.1': 'completed',
        '2.2': 'ongoing',
        '2.3': 'scheduled',
        '3': 'scheduled',
        '4': 'scheduled',
        '4.1': 'scheduled',
    }
