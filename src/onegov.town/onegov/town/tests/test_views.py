import json
import onegov.core
import onegov.town
import re

from base64 import b64decode, b64encode
from onegov.testing import utils
from webtest import (
    TestApp as BaseApp,
    TestResponse as BaseResponse,
    TestRequest as BaseRequest
)


class SkipFirstForm(object):

    @property
    def form(self):
        """ Ignore the first form, which is the general search form on
        the top of the page.

        """
        if len(self.forms) > 1:
            return self.forms[1]
        else:
            return super().form


class Response(SkipFirstForm, BaseResponse):
    pass


class Request(SkipFirstForm, BaseRequest):
    ResponseClass = Response


class Client(SkipFirstForm, BaseApp):
    RequestClass = Request

    def login(self, username, password, to):
        url = '/auth/login' + (to and ('/?to=' + to) or '')

        login_page = self.get(url)
        login_page.form.set('username', username)
        login_page.form.set('password', password)
        return login_page.form.submit()

    def login_admin(self, to=None):
        return self.login('admin@example.org', 'hunter2', to)

    def login_editor(self, to=None):
        return self.login('editor@example.org', 'hunter2', to)

    def logout(self):
        return self.get('/auth/logout')


def get_message(app, index, payload=0):
    message = app.smtp.outbox[index]
    message = message.get_payload(payload).get_payload(decode=True)
    return message.decode('iso-8859-1')


def extract_href(link):
    """ Takes a link (<a href...>) and returns the href address. """
    result = re.search(r'(?:href|ic-delete-from)="([^"]+)', link)

    return result and result.group(1) or None


def select_checkbox(page, groupname, label, form=None, checked=True):
    """ Selects one of many checkboxes by fuzzy searching the label next to
    it. Webtest is not good enough in this regard.

    Selects the checkbox from the form returned by page.form, or the given
    form if passed. In any case, the form needs to be part of the page.

    """

    elements = page.pyquery('input[name="{}"]'.format(groupname))
    form = form or page.form

    for ix, el in enumerate(elements):
        if label in el.label.text_content():
            form.get(groupname, index=ix).value = checked


def encode_map_value(dictionary):
    return b64encode(json.dumps(dictionary).encode('utf-8'))


def decode_map_value(value):
    return json.loads(b64decode(value).decode('utf-8'))


def bound_reserve(client, allocation):

    default_start = '{:%H:%M}'.format(allocation.start)
    default_end = '{:%H:%M}'.format(allocation.end)
    default_whole_day = allocation.whole_day
    resource = allocation.resource
    allocation_id = allocation.id

    def reserve(
        start=default_start,
        end=default_end,
        quota=1,
        whole_day=default_whole_day
    ):

        baseurl = '/einteilung/{}/{}/reserve'.format(
            resource,
            allocation_id
        )
        query = '?start={start}&end={end}&quota={quota}&whole_day={whole_day}'

        return client.post(baseurl + query.format(
            start=start,
            end=end,
            quota=quota,
            whole_day=whole_day and '1' or '0')
        )

    return reserve


def test_view_permissions():
    utils.assert_explicit_permissions(onegov.town, onegov.town.TownApp)


def test_startpage(town_app):
    client = Client(town_app)

    links = client.get('/').pyquery('.top-bar-section a')

    assert links[0].text == 'Bildung & Gesellschaft'
    assert links[0].attrib.get('href').endswith('/themen/bildung-gesellschaft')

    assert links[1].text == 'Gewerbe & Tourismus'
    assert links[1].attrib.get('href').endswith('/themen/gewerbe-tourismus')

    assert links[2].text == 'Kultur & Freizeit'
    assert links[2].attrib.get('href').endswith('/themen/kultur-freizeit')

    assert links[3].text == 'Leben & Wohnen'
    assert links[3].attrib.get('href').endswith('/themen/leben-wohnen')

    assert links[4].text == 'Politik & Verwaltung'
    assert links[4].attrib.get('href').endswith('/themen/politik-verwaltung')

    links = client.get('/').pyquery('.homepage-tiles a')

    assert links[0].find('h3').text == 'Bildung & Gesellschaft'
    assert links[0].attrib.get('href').endswith('/themen/bildung-gesellschaft')

    assert links[1].find('h3').text == 'Gewerbe & Tourismus'
    assert links[1].attrib.get('href').endswith('/themen/gewerbe-tourismus')

    assert links[2].find('h3').text == 'Kultur & Freizeit'
    assert links[2].attrib.get('href').endswith('/themen/kultur-freizeit')

    assert links[3].find('h3').text == 'Leben & Wohnen'
    assert links[3].attrib.get('href').endswith('/themen/leben-wohnen')

    assert links[4].find('h3').text == 'Politik & Verwaltung'
    assert links[4].attrib.get('href').endswith('/themen/politik-verwaltung')

    assert links[5].find('h3').text == 'Aktuelles'
    assert links[5].attrib.get('href').endswith('/aktuelles')


def test_view_occurrences_on_startpage(town_app):
    client = Client(town_app)
    links = [
        a.text for a in client.get('/').pyquery('.homepage-links-panel li a')
    ]
    events = (
        '150 Jahre Govikon',
        'Alle Veranstaltungen',
        'Gemeindeversammlung',
        'MuKi Turnen',
    )
    assert set(events) <= set(links)


def test_pages_on_homepage(es_town_app):
    client = Client(es_town_app)

    client.login_editor()

    new_page = client.get('/themen/bildung-gesellschaft').click('Thema')
    new_page.form['title'] = "0xdeadbeef"
    new_page = new_page.form.submit().follow()

    assert '0xdeadbeef' not in client.get('/')

    edit_page = new_page.click('Bearbeiten')
    edit_page.form['is_visible_on_homepage'] = True
    edit_page.form.submit()

    assert '0xdeadbeef' in client.get('/')

    edit_page = new_page.click('Bearbeiten')
    edit_page.form['is_hidden_from_public'] = True
    edit_page.form.submit()

    assert '0xdeadbeef' in client.get('/')
    assert '0xdeadbeef' not in Client(es_town_app).get('/')

    client.delete(
        new_page.pyquery('a[ic-delete-from]')[0].attrib['ic-delete-from']
    )

    assert '0xdeadbeef' not in client.get('/')
