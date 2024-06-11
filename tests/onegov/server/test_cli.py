import port_for
import requests
import time

from onegov.server.cli import WsgiProcess, WsgiServer
from wsgiref.simple_server import demo_app
from pytest import fixture
from multiprocessing import get_start_method, set_start_method


@fixture
def use_spawn_process():
    # the default start method (fork) might lead to deadlocks if the current
    # process is multi-threaded (which it is due to pytest-rerunfailures).
    start_method = get_start_method(allow_none=True)
    set_start_method('spawn')
    yield
    set_start_method(start_method, force=True)


def app_factory():
    return demo_app


def test_wsgi_process(use_spawn_process):
    port = port_for.select_random()

    process = WsgiProcess(app_factory, port=port)
    process.start()

    while not process.ready:
        time.sleep(0.1)

    response = requests.get(f'http://127.0.0.1:{port}')
    assert response.status_code == 200
    assert "Hello world!" in response.content.decode('utf-8')

    process.terminate()


def test_wsgi_server(use_spawn_process):
    port = port_for.select_random()

    server = WsgiServer(app_factory, port=port)
    server.start()

    while not server.process.ready:
        time.sleep(0.1)

    original_pid = server.process.pid

    response = requests.get(f'http://127.0.0.1:{port}')
    assert response.status_code == 200
    assert "Hello world!" in response.content.decode('utf-8')

    class MockEvent:
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
