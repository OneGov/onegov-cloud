""" Provides testing tools for other organisation apps. """
import json
import re

from base64 import b64decode, b64encode

# XXX we're using testing modules here, luckily webtest is used by the core
# outside the tests extra anyway, but going forward we shouldn't add test
# dependencies here -> this module is really just an exception because
# we don't want tests/ to include an __init__.py file, so we have to
# put some code outside if we want it to be reusable by other modules
from webtest import TestApp as BaseApp
from webtest import TestRequest as BaseRequest
from webtest import TestResponse as BaseResponse


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

    def login(self, username, password, to=None):
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
    return message.decode('utf-8')


def extract_href(link):
    """ Takes a link (<a href...>) and returns the href address. """
    result = re.search(r'(?:href|ic-post-to|ic-delete-from)="([^"]+)', link)

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
