import port_for
import requests
import time

from onegov.server.cli import WsgiProcess, WsgiServer
from wsgiref.simple_server import demo_app


def test_wsgi_process():
    port = port_for.select_random()

    process = WsgiProcess(lambda: demo_app, port=port)
    process.start()

    while not process.ready:
        time.sleep(0.1)

    response = requests.get(f'http://127.0.0.1:{port}')
    assert response.status_code == 200
    assert "Hello world!" in response.content.decode('utf-8')

    process.terminate()


def test_wsgi_server():
    port = port_for.select_random()

    server = WsgiServer(lambda: demo_app, port=port)
    server.start()

    while not server.process.ready:
        time.sleep(0.1)

    original_pid = server.process.pid

    response = requests.get(f'http://127.0.0.1:{port}')
    assert response.status_code == 200
    assert "Hello world!" in response.content.decode('utf-8')

    class MockEvent(object):
        src_path = None
        is_directory = False

    event = MockEvent()
    event.src_path = 'test.py'
    server.on_any_event(event)

    while not server.process.ready:
        time.sleep(0.1)

    assert server.process.pid != original_pid

    response = requests.get(f'http://127.0.0.1:{port}')
    assert response.status_code == 200
    assert "Hello world!" in response.content.decode('utf-8')

    server.stop()
