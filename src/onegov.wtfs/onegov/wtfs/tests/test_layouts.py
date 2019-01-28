from onegov.wtfs.layouts import DefaultLayout
from onegov.wtfs.layouts import MailLayout


class DummyPrincipal(object):
    pass


class DummyApp(object):
    principal = DummyPrincipal()
    theme_options = {}


class DummyRequest(object):
    app = DummyApp()
    is_logged_in = False
    locale = 'de_CH'
    roles = []
    includes = []
    session = None
    url = ''

    def has_role(self, *roles):
        return any((role in self.roles for role in roles))

    def translate(self, text):
        return str(text)

    def include(self, *args, **kwargs):
        self.includes.extend(args)

    def link(self, model, name=''):
        if isinstance(model, str):
            return f'{model}/{name}'
        return f'{model.__class__.__name__}/{name}'

    def exclude_invisible(self, objects):
        return objects

    def new_csrf_token(self):
        return 'x'


def test_layout_default(wtfs_app):
    request = DummyRequest()
    request.app = wtfs_app
    request.session = wtfs_app.session()
    model = None

    layout = DefaultLayout(model, request)
    assert layout.title == ""
    assert layout.editbar_links == []
    assert layout.breadcrumbs == [('Homepage', 'Principal/', 'current')]
    assert layout.static_path == 'Principal/static'
    assert layout.app_version
    assert layout.request.includes == ['frameworks', 'chosen', 'common']
    assert layout.top_navigation == []
    assert layout.homepage_link == 'Principal/'
    assert layout.login_link == 'Auth/login'
    assert layout.logout_link is None

    # Login
    request.is_logged_in = True
    layout = DefaultLayout(model, request)
    assert layout.login_link is None
    assert layout.logout_link == 'Auth/logout'


def test_layout_mail():
    request = DummyRequest()
    model = None

    layout = MailLayout(model, request)
    assert layout.primary_color == '#fff'
