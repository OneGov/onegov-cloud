from onegov.landsgemeinde.models import Assembly, Votum
from transaction import commit


def test_ticker(browser, assembly):
    app = browser.wsgi_server.app
    app.session().add(assembly)
    commit()

    browser.visit('/landsgemeinde/2023-05-07/ticker')
    assert browser.websocket_server_url in browser.html

    # refresh
    assembly = app.session().query(Assembly).one()
    assembly.overview = 'Lorem ipsum'
    assembly.agenda_items[0].title = 'Adipiscing elit'
    commit()

    # ... wrong date
    app.send_websocket({
        'event': 'refresh',
        'assembly': '2023-05-06'
    })
    assert 'Lorem ipsum' not in browser.html
    assert 'Adipiscing elit' not in browser.html

    # ... correct date
    app.send_websocket({
        'event': 'refresh',
        'assembly': '2023-05-07'
    })
    assert 'Lorem ipsum' in browser.html
    assert 'Adipiscing elit' in browser.html

    # update
    assembly = app.session().query(Assembly).one()
    assembly.overview = 'Dolor sit amet'
    assembly.agenda_items[0].title = 'Eiusmod tempor'
    commit()

    # ... wrong date
    app.send_websocket({
        'event': 'update',
        'assembly': '2023-05-06',
        'node': 'agenda-item-2',
        'content': 'Consectetur'
    })
    assert 'Lorem ipsum' in browser.html
    assert 'Dolor sit amet' not in browser.html
    assert 'Adipiscing elit' in browser.html
    assert 'Eiusmod tempor' not in browser.html
    assert 'Consectetur' not in browser.html

    # ... correct date
    app.send_websocket({
        'event': 'update',
        'assembly': '2023-05-07',
        'node': 'agenda-item-2',
        'content': 'Consectetur'
    })
    assert 'Lorem ipsum' in browser.html
    assert 'Dolor sit amet' not in browser.html
    assert 'Adipiscing elit' in browser.html
    assert 'Eiusmod tempor' not in browser.html
    assert 'Consectetur' in browser.html


def test_timestamp_update_in_iframe(browser, assembly):
    app = browser.wsgi_server.app
    app.session().add(assembly)
    commit()

    assembly = app.session().query(Assembly).one()
    assembly.state = 'completed'
    assembly.video_url = 'https://example.com'
    votum = app.session().query(Votum).filter_by(number=3).one()
    votum.state = 'completed'
    votum.video_timestamp = "1h2m3s"
    commit()

    browser.visit('/traktandum/2023-05-07/2')
    assert '1h2m3s' in browser.html
    browser.find_by_css('.video-link a').first.click()
    # browser.find_by_value('1h2m3s').click()
