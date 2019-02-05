from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.layouts import AddMunicipalityLayout
from onegov.wtfs.layouts import AddUserGroupLayout
from onegov.wtfs.layouts import AddUserLayout
from onegov.wtfs.layouts import DefaultLayout
from onegov.wtfs.layouts import EditMunicipalityLayout
from onegov.wtfs.layouts import EditUserGroupLayout
from onegov.wtfs.layouts import EditUserLayout
from onegov.wtfs.layouts import MailLayout
from onegov.wtfs.layouts import MunicipalitiesLayout
from onegov.wtfs.layouts import MunicipalityLayout
from onegov.wtfs.layouts import UserGroupLayout
from onegov.wtfs.layouts import UserGroupsLayout
from onegov.wtfs.layouts import UserLayout
from onegov.wtfs.layouts import UsersLayout
from onegov.wtfs.models import Municipality
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted
from onegov.wtfs.security import ViewModel


class DummyPrincipal(object):
    pass


class DummyApp(object):
    principal = DummyPrincipal()
    theme_options = {}


class DummyRequest(object):
    app = DummyApp()
    is_logged_in = False
    locale = 'de_CH'
    url = ''

    def __init__(self, session=None, roles=[], includes=[], permissions=[]):
        self.session = session
        self.roles = roles
        self.permissions = permissions
        self.includes = includes

    def has_role(self, *roles):
        return any((role in self.roles for role in roles))

    def has_permission(self, model, permission):
        if self.has_role('admin'):
            return permission in {
                AddModel,
                AddModelUnrestricted,
                DeleteModel,
                EditModel,
                EditModelUnrestricted,
                ViewModel
            }
        if self.has_role('editor'):
            return permission in {
                AddModel,
                DeleteModel,
                EditModel,
                ViewModel
            }
        return permission in self.permissions

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


def path(links):
    return '/'.join([link.attrs['href'].strip('/') for link in links])


def hrefs(items):
    for item in items:
        if hasattr(item, 'links'):
            for ln in item.links:
                yield (
                    ln.attrs.get('href')
                    or ln.attrs.get('ic-delete-from')
                    or ln.attrs.get('ic-post-to')
                )
        else:
            yield (
                item.attrs.get('href')
                or item.attrs.get('ic-delete-from')
                or item.attrs.get('ic-post-to')
            )


def test_default_layout(wtfs_app):
    request = DummyRequest()
    request.app = wtfs_app
    request.session = wtfs_app.session()
    model = None

    layout = DefaultLayout(model, request)
    assert layout.title == ""
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'Principal'
    assert layout.static_path == 'Principal/static'
    assert layout.app_version
    assert layout.request.includes == ['frameworks', 'chosen', 'common']
    assert layout.top_navigation == []
    assert layout.cancel_url == ''
    assert layout.success_url == ''
    assert layout.homepage_url == 'Principal/'
    assert layout.login_url == 'Auth/login'
    assert layout.logout_url is None
    assert layout.user_groups_url == 'UserGroupCollection/'
    assert layout.users_url == 'UserCollection/'
    assert layout.municipalities_url == 'MunicipalityCollection/'

    # Login
    request.is_logged_in = True
    layout = DefaultLayout(model, request)
    assert layout.login_url is None
    assert layout.logout_url == 'Auth/logout'


def test_mail_layout():
    request = DummyRequest()
    model = None

    layout = MailLayout(model, request)
    assert layout.primary_color == '#fff'


def test_municipality_layouts():
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])

    # Municipality collection
    model = MunicipalityCollection(None)
    layout = MunicipalitiesLayout(model, request)
    assert layout.title == 'Municipalities'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/MunicipalityCollection'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = MunicipalitiesLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == ['MunicipalityCollection/add']

    # .. add
    layout = AddMunicipalityLayout(model, request)
    assert layout.title == 'Add'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/#'
    )
    assert layout.cancel_url == 'MunicipalityCollection/'
    assert layout.success_url == 'MunicipalityCollection/'

    layout = AddMunicipalityLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    # Municipality
    model = Municipality(name='Winterthur')
    layout = MunicipalityLayout(model, request)
    assert layout.title == 'Winterthur'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/#'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = MunicipalityLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'Municipality/edit',
        'Municipality/?csrf-token=x'
    ]

    # ... edit
    layout = EditMunicipalityLayout(model, request)
    assert layout.title == 'Edit'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/Municipality/#'
    )
    assert layout.cancel_url == 'Municipality/'
    assert layout.success_url == 'MunicipalityCollection/'

    layout = EditMunicipalityLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []


def test_user_group_layouts():
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])

    # User group collection
    model = UserGroupCollection(None)
    layout = UserGroupsLayout(model, request)
    assert layout.title == 'User groups'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/UserGroupCollection'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = UserGroupsLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == ['UserGroupCollection/add']

    # .. add
    layout = AddUserGroupLayout(model, request)
    assert layout.title == 'Add'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/UserGroupCollection/#'
    )
    assert layout.cancel_url == 'UserGroupCollection/'
    assert layout.success_url == 'UserGroupCollection/'

    layout = AddUserGroupLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    # User group
    model = UserGroup(name='Winterthur')
    layout = UserGroupLayout(model, request)
    assert layout.title == 'Winterthur'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/UserGroupCollection/#'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = UserGroupLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'UserGroup/edit',
        'UserGroup/?csrf-token=x'
    ]

    # ... edit
    layout = EditUserGroupLayout(model, request)
    assert layout.title == 'Edit'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/UserGroupCollection/UserGroup/#'
    )
    assert layout.cancel_url == 'UserGroup/'
    assert layout.success_url == 'UserGroupCollection/'

    layout = EditUserGroupLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []


def test_user_layouts():
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])
    request_editor = DummyRequest(roles=['editor'])

    # User collection
    model = UserCollection(None)
    layout = UsersLayout(model, request)
    assert layout.title == 'Users'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/UserCollection'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = UsersLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'UserCollection/add-unrestricted'
    ]

    layout = UsersLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == ['UserCollection/add']

    # .. add
    layout = AddUserLayout(model, request)
    assert layout.title == 'Add'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/UserCollection/#'
    )
    assert layout.cancel_url == 'UserCollection/'
    assert layout.success_url == 'UserCollection/'

    layout = AddUserLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    layout = AddUserLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == []

    # User
    model = User(
        realname='Hans Muster',
        username="hans.muster@winterthur.ch",
        role='member',
        password='1234'
    )
    layout = UserLayout(model, request)
    assert layout.title == 'Hans Muster'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/UserCollection/#'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = UserLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'User/edit-unrestricted',
        'User/?csrf-token=x'
    ]

    layout = UserLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == [
        'User/edit',
        'User/?csrf-token=x'
    ]

    # ... edit
    layout = EditUserLayout(model, request)
    assert layout.title == 'Edit'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/UserCollection/User/#'
    assert layout.cancel_url == 'User/'
    assert layout.success_url == 'UserCollection/'

    layout = EditUserLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    layout = EditUserLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == []
