from datetime import date
from freezegun import freeze_time
from lxml import etree
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import Votum
from onegov.landsgemeinde.utils import ensure_states, seconds_to_timestamp
from onegov.landsgemeinde.utils import timestamp_to_seconds
from onegov.landsgemeinde.utils import update_ticker


def test_update_ticker(landsgemeinde_app, assembly):

    class Request:
        app = landsgemeinde_app
        is_manager = True
        url = 'http://localhost'
        locale = 'de_CH'
        template_loader = (
            landsgemeinde_app.config
            .template_engine_registry
            ._template_loaders['.pt']
        )

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
    etree.fromstring(calls[5]['content'], parser=etree.HTMLParser())
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
            f'{a.number}.{v.number}': f'{v.state} {v.start_time or ""}'.strip()
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

    # 1 draft
    assembly = create()
    assembly.agenda_items[0].state = 'draft'
    assert ensure_states(assembly.agenda_items[0]) == {
        assembly,  # was completed
        assembly.agenda_items[0].vota[0],  # was completed
        assembly.agenda_items[0].vota[1],  # was completed
        assembly.agenda_items[0].vota[2],  # was completed
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[0],  # was completed
        assembly.agenda_items[1].vota[1],  # was ongoing
        assembly.agenda_items[1].vota[2],  # was ongoing
        assembly.agenda_items[2],  # was scheduled
        assembly.agenda_items[3],  # was scheduled
        assembly.agenda_items[3].vota[0],  # was scheduled
        assembly.agenda_items[3].vota[1],  # was scheduled
    }
    assert get(assembly) == {
        '': 'draft',
        '1': 'draft',
        '1.1': 'draft',
        '1.2': 'draft',
        '1.3': 'draft',
        '2': 'draft',
        '2.1': 'draft',
        '2.2': 'draft',
        '2.3': 'draft',
        '3': 'draft',
        '4': 'draft',
        '4.1': 'draft',
        '4.2': 'draft'
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
        assembly.agenda_items[0].vota[1],  # start set
        assembly.agenda_items[0].vota[2],  # was completed
        assembly.agenda_items[1],  # was ongoing
        assembly.agenda_items[1].vota[0],  # was completed
        assembly.agenda_items[1].vota[1],  # was ongoing
    }
    assert get(assembly) == {
        '': 'ongoing',
        '1': 'ongoing 12:00:00',
        '1.1': 'completed',
        '1.2': 'ongoing 12:00:00',
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
        assembly.agenda_items[1].vota[2],  # start set
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
        '2.3': 'ongoing 12:00:00',
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
        assembly.agenda_items[3].vota[0],  # start set
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
        '4.1': 'ongoing 12:00:00',
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
        assembly.agenda_items[3].vota[2],  # start set
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
        '4.3': 'ongoing 12:00:00'
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


def test_timestamps_to_seconds():
    assert timestamp_to_seconds(None) is None
    assert timestamp_to_seconds('') is None

    assert timestamp_to_seconds('1h2m3s') == 3723
    assert timestamp_to_seconds('1h1m') == 3660
    assert timestamp_to_seconds('1h2s') == 3602
    assert timestamp_to_seconds('1h') == 3600
    assert timestamp_to_seconds('1m3s') == 63
    assert timestamp_to_seconds('1m') == 60
    assert timestamp_to_seconds('5s') == 5

    assert timestamp_to_seconds('01h02m03s') == 3723
    assert timestamp_to_seconds('02m03s') == 123
    assert timestamp_to_seconds('05s') == 5

    assert timestamp_to_seconds('10h20m30s') == 37230
    assert timestamp_to_seconds('20m30s') == 1230
    assert timestamp_to_seconds('50s') == 50

    assert timestamp_to_seconds('-50s') is None
    assert timestamp_to_seconds('100h200m300s') is None
    assert timestamp_to_seconds('foo2m3s') is None
    assert timestamp_to_seconds('2m3sfoo') is None
    assert timestamp_to_seconds('s10') is None
    assert timestamp_to_seconds('hms') is None
    assert timestamp_to_seconds('foo') is None


def test_seconds_to_timestamp():
    assert seconds_to_timestamp(None) == '0s'
    assert seconds_to_timestamp(0) == '0s'
    assert seconds_to_timestamp(1) == '1s'
    assert seconds_to_timestamp(60) == '1m'
    assert seconds_to_timestamp(61) == '1m1s'
    assert seconds_to_timestamp(1230) == '20m30s'
    assert seconds_to_timestamp(37230) == '10h20m30s'
    assert seconds_to_timestamp(3601) == '1h1s'
    assert seconds_to_timestamp(-500) == '0s'
