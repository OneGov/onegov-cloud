from datetime import date
from onegov.user import User
from onegov.user import UserCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import NotificationCollection
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.layouts import AddMunicipalityLayout
from onegov.wtfs.layouts import AddNotificationLayout
from onegov.wtfs.layouts import AddScanJobLayout
from onegov.wtfs.layouts import AddUserLayout
from onegov.wtfs.layouts import DailyListBoxesAndFormsLayout
from onegov.wtfs.layouts import DailyListBoxesLayout
from onegov.wtfs.layouts import DailyListLayout
from onegov.wtfs.layouts import DefaultLayout
from onegov.wtfs.layouts import DeleteMunicipalityDatesLayout
from onegov.wtfs.layouts import DeliveryNoteLayout
from onegov.wtfs.layouts import EditMunicipalityLayout
from onegov.wtfs.layouts import EditNotificationLayout
from onegov.wtfs.layouts import EditScanJobLayout
from onegov.wtfs.layouts import EditUserLayout
from onegov.wtfs.layouts import EditUserManualLayout
from onegov.wtfs.layouts import ImportMunicipalityDataLayout
from onegov.wtfs.layouts import InvoiceLayout
from onegov.wtfs.layouts import MailLayout
from onegov.wtfs.layouts import MunicipalitiesLayout
from onegov.wtfs.layouts import MunicipalityLayout
from onegov.wtfs.layouts import NotificationLayout
from onegov.wtfs.layouts import NotificationsLayout
from onegov.wtfs.layouts import PaymentTypesLayout
from onegov.wtfs.layouts import ReportBoxesAndFormsByDeliveryLayout
from onegov.wtfs.layouts import ReportBoxesAndFormsLayout
from onegov.wtfs.layouts import ReportBoxesLayout
from onegov.wtfs.layouts import ReportFormsByMunicipalityLayout
from onegov.wtfs.layouts import ReportLayout
from onegov.wtfs.layouts import ScanJobLayout
from onegov.wtfs.layouts import ScanJobsLayout
from onegov.wtfs.layouts import UserLayout
from onegov.wtfs.layouts import UserManualLayout
from onegov.wtfs.layouts import UsersLayout
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import DailyListBoxesAndForms
from onegov.wtfs.models import Invoice
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Notification
from onegov.wtfs.models import Report
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportBoxesAndFormsByDelivery
from onegov.wtfs.models import ReportFormsByMunicipality
from onegov.wtfs.models import UserManual
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
    assert layout.users_url == 'UserCollection/'
    assert layout.municipalities_url == 'MunicipalityCollection/'
    assert layout.scan_jobs_url == 'ScanJobCollection/'
    assert layout.payment_types_url == 'PaymentTypeCollection/'
    assert layout.current_year == date.today().year

    # Login
    request.is_logged_in = True
    request.roles = ['admin']
    layout = DefaultLayout(model, request)
    assert layout.login_url is None
    assert layout.logout_url == 'Auth/logout'
    assert list(hrefs(layout.top_navigation)) == [
        'ScanJobCollection/',
        'DailyList/',
        'Report/',
        'Invoice/',
        'UserCollection/',
        'MunicipalityCollection/',
        'NotificationCollection/',
        'UserManual/'
    ]


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
    assert list(hrefs(layout.editbar_links)) == [
        'MunicipalityCollection/import-data',
        'MunicipalityCollection/add'
    ]

    # ... add
    layout = AddMunicipalityLayout(model, request)
    assert layout.title == 'Add municipality'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/#'
    )
    assert layout.cancel_url == 'MunicipalityCollection/'
    assert layout.success_url == 'MunicipalityCollection/'

    layout = AddMunicipalityLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    # ... import data
    layout = ImportMunicipalityDataLayout(model, request)
    assert layout.title == 'Import data'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/#'
    )
    assert layout.cancel_url == 'MunicipalityCollection/'
    assert layout.success_url == 'MunicipalityCollection/'

    layout = ImportMunicipalityDataLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    # Municipality
    model = Municipality(name='Boppelsen')
    layout = MunicipalityLayout(model, request)
    assert layout.title == 'Boppelsen'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/#'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = MunicipalityLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'Municipality/edit',
        'Municipality/delete-dates',
        'Municipality/?csrf-token=x'
    ]

    # ... edit
    layout = EditMunicipalityLayout(model, request)
    assert layout.title == 'Edit municipality'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/Municipality/#'
    )
    assert layout.cancel_url == 'Municipality/'
    assert layout.success_url == 'MunicipalityCollection/'

    layout = EditMunicipalityLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    # ... delete dates
    layout = DeleteMunicipalityDatesLayout(model, request)
    assert layout.title == 'Delete pick-up dates'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/MunicipalityCollection/Municipality/#'
    )
    assert layout.cancel_url == 'Municipality/'
    assert layout.success_url == 'Municipality/'

    layout = DeleteMunicipalityDatesLayout(model, request_admin)
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
    assert layout.title == 'Add user'
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
    assert layout.title == 'Edit user'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/UserCollection/User/#'
    assert layout.cancel_url == 'User/'
    assert layout.success_url == 'UserCollection/'

    layout = EditUserLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    layout = EditUserLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == []


def test_scan_job_layouts(session):
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])
    request_editor = DummyRequest(roles=['editor'])

    municipalities = MunicipalityCollection(session)
    municipality = municipalities.add(name='Boppelsen', bfs_number=82)

    # ScanJob collection
    model = ScanJobCollection(None)
    layout = ScanJobsLayout(model, request)
    assert layout.title == 'Scan jobs'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/ScanJobCollection'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = ScanJobsLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'ScanJobCollection/add-unrestricted'
    ]

    layout = ScanJobsLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == ['ScanJobCollection/add']

    # .. add
    layout = AddScanJobLayout(model, request)
    assert layout.title == 'Add scan job'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/ScanJobCollection/#'
    assert layout.cancel_url == 'ScanJobCollection/'
    assert layout.success_url == 'ScanJobCollection/'

    layout = AddScanJobLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    layout = AddScanJobLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == []

    # ScanJob
    model = ScanJobCollection(session).add(
        type='normal',
        dispatch_date=date(2019, 1, 1),
        municipality_id=municipality.id
    )
    layout = ScanJobLayout(model, request)
    assert layout.title.interpolate() == 'Scan job no. 1'
    assert list(hrefs(layout.editbar_links)) == ['ScanJob/delivery-note']
    assert path(layout.breadcrumbs) == 'DummyPrincipal/ScanJobCollection/#'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = ScanJobLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'ScanJob/delivery-note',
        'ScanJob/edit-unrestricted',
        'ScanJob/?csrf-token=x'
    ]

    layout = ScanJobLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == [
        'ScanJob/delivery-note',
        'ScanJob/edit',
        'ScanJob/?csrf-token=x'
    ]

    # ... edit
    layout = EditScanJobLayout(model, request)
    assert layout.title == 'Edit scan job'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/ScanJobCollection/ScanJob/#'
    )
    assert layout.cancel_url == 'ScanJob/'
    assert layout.success_url == 'ScanJob/'

    layout = EditScanJobLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    layout = EditScanJobLayout(model, request_editor)
    assert list(hrefs(layout.editbar_links)) == []

    # ... delivery note
    layout = DeliveryNoteLayout(model, request)
    assert layout.title == 'Delivery note'
    assert list(hrefs(layout.editbar_links)) == ['#']
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/ScanJobCollection/ScanJob/#'
    )


def test_daily_list_layouts(session):
    request = DummyRequest()

    model = DailyList()
    layout = DailyListLayout(model, request)
    assert layout.title == 'Daily list'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/DailyList'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    model = DailyListBoxes(session, date_=date(2019, 1, 1))
    layout = DailyListBoxesLayout(model, request)
    assert layout.title == 'Boxes'
    assert layout.subtitle == 'Dienstag 01. Januar 2019'
    assert list(hrefs(layout.editbar_links)) == ['#']
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/DailyList/#/DailyListBoxes'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    model = DailyListBoxesAndForms(session, date_=date(2019, 1, 1))
    layout = DailyListBoxesAndFormsLayout(model, request)
    assert layout.title == 'Boxes and forms'
    assert layout.subtitle == 'Dienstag 01. Januar 2019'
    assert list(hrefs(layout.editbar_links)) == ['#']
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/DailyList/#/DailyListBoxesAndForms'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''


def test_report_layouts(session):
    municipality = MunicipalityCollection(session).add(
        name="Adlikon",
        bfs_number=21,
    )

    request = DummyRequest()

    model = Report(session)
    layout = ReportLayout(model, request)
    assert layout.title == 'Report'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/Report'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    model = ReportBoxes(
        session,
        start=date(2019, 1, 1),
        end=date(2019, 1, 31)
    )
    layout = ReportBoxesLayout(model, request)
    assert layout.title == 'Report boxes'
    assert layout.subtitle == '01.01.2019-31.01.2019'
    assert list(hrefs(layout.editbar_links)) == ['#']
    assert path(layout.breadcrumbs) == 'DummyPrincipal/Report/#/ReportBoxes'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    model = ReportBoxesAndForms(
        session,
        start=date(2019, 1, 1),
        end=date(2019, 1, 31)
    )
    layout = ReportBoxesAndFormsLayout(model, request)
    assert layout.title == 'Report boxes and forms'
    assert layout.subtitle == '01.01.2019-31.01.2019'
    assert list(hrefs(layout.editbar_links)) == ['#']
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/Report/#/ReportBoxesAndForms'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    model = ReportFormsByMunicipality(
        session,
        start=date(2019, 1, 1),
        end=date(2019, 1, 31),
        municipality_id=municipality.id
    )
    layout = ReportFormsByMunicipalityLayout(model, request)
    assert layout.title == 'Report forms'
    assert layout.subtitle == 'Adlikon 01.01.2019-31.01.2019'
    assert list(hrefs(layout.editbar_links)) == ['#']
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/Report/#/ReportFormsByMunicipality'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    model = ReportBoxesAndFormsByDelivery(
        session,
        start=date(2019, 1, 1),
        end=date(2019, 1, 31),
        type='normal',
        municipality_id=municipality.id
    )
    layout = ReportBoxesAndFormsByDeliveryLayout(model, request)
    assert layout.title == 'Report boxes and forms by delivery'
    assert layout.subtitle == 'Adlikon (21) 01.01.2019-31.01.2019'
    assert list(hrefs(layout.editbar_links)) == ['#']
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/Report/#/ReportBoxesAndFormsByDelivery'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''


def test_notification_layouts():
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])

    # Notification collection
    model = NotificationCollection(None)
    layout = NotificationsLayout(model, request)
    assert layout.title == 'Notifications'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/NotificationCollection'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = NotificationsLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == ['NotificationCollection/add']

    # .. add
    layout = AddNotificationLayout(model, request)
    assert layout.title == 'Add notification'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/NotificationCollection/#'
    )
    assert layout.cancel_url == 'NotificationCollection/'
    assert layout.success_url == 'NotificationCollection/'

    layout = AddNotificationLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []

    # Notification
    model = Notification(title="Title")
    layout = NotificationLayout(model, request)
    assert layout.title == 'Title'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/NotificationCollection/#'
    )
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = NotificationLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'Notification/edit',
        'Notification/?csrf-token=x'
    ]

    # ... edit
    layout = EditNotificationLayout(model, request)
    assert layout.title == 'Edit notification'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == (
        'DummyPrincipal/NotificationCollection/Notification/#'
    )
    assert layout.cancel_url == 'Notification/'
    assert layout.success_url == 'Notification/'

    layout = EditNotificationLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []


def test_invoice_layouts(session):
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])

    model = Invoice(session)
    layout = InvoiceLayout(model, request)
    assert layout.title == 'Create invoice'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/Invoice'
    assert layout.cancel_url == 'Invoice/'
    assert layout.success_url == 'Invoice/'

    layout = InvoiceLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'PaymentTypeCollection/',
    ]


def test_payments_type_layouts(session):
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])

    model = PaymentTypeCollection(session)
    layout = PaymentTypesLayout(model, request)
    assert layout.title == 'Manage payment types'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/PaymentTypeCollection'
    assert layout.cancel_url == 'Invoice/'
    assert layout.success_url == 'Invoice/'

    layout = PaymentTypesLayout(model, request_admin)
    assert layout.editbar_links == []


def test_user_manual_layouts():
    request = DummyRequest()
    request_admin = DummyRequest(roles=['admin'])

    # UserManualLayout
    model = UserManual(object)
    layout = UserManualLayout(None, request)
    assert layout.title == 'User manual'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/#'
    assert layout.cancel_url == ''
    assert layout.success_url == ''

    layout = UserManualLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == [
        'UserManual/edit',
    ]

    # ... edit
    layout = EditUserManualLayout(model, request)
    assert layout.title == 'Edit user manual'
    assert layout.editbar_links == []
    assert path(layout.breadcrumbs) == 'DummyPrincipal/UserManual/#'
    assert layout.cancel_url == 'UserManual/'
    assert layout.success_url == 'UserManual/'

    layout = EditUserManualLayout(model, request_admin)
    assert list(hrefs(layout.editbar_links)) == []
