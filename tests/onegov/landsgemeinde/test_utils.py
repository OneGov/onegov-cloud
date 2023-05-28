from onegov.landsgemeinde.utils import update_ticker
from unittest.mock import Mock
from lxml import etree


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
