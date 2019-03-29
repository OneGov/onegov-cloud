from onegov.core.converters import extended_date_converter
from onegov.core.converters import uuid_converter
from onegov.user import Auth
from onegov.user import User
from onegov.user import UserCollection
from onegov.wtfs.app import WtfsApp
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import NotificationCollection
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import DailyListBoxesAndForms
from onegov.wtfs.models import Invoice
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Notification
from onegov.wtfs.models import Principal
from onegov.wtfs.models import Report
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportBoxesAndFormsByDelivery
from onegov.wtfs.models import ReportFormsByMunicipality
from onegov.wtfs.models import ScanJob
from webob.exc import HTTPNotFound


@WtfsApp.path(
    model=Principal,
    path='/'
)
def get_principal(app):
    return app.principal


@WtfsApp.path(
    model=Auth,
    path='/auth'
)
def get_auth(request, to='/'):
    return Auth.from_request(request, to)


@WtfsApp.path(
    model=UserCollection,
    path='/users'
)
def get_users(request):
    return UserCollection(request.session)


@WtfsApp.path(
    model=User,
    path='/user/{username}'
)
def get_user(request, username):
    return UserCollection(request.session).by_username(username)


@WtfsApp.path(
    model=MunicipalityCollection,
    path='/municipalities'
)
def get_municipalities(request):
    return MunicipalityCollection(request.session)


@WtfsApp.path(
    model=Municipality,
    path='/municipality/{id}',
    converters=dict(
        id=uuid_converter
    )
)
def get_municipality(request, id):
    return MunicipalityCollection(request.session).by_id(id)


@WtfsApp.path(
    model=ScanJobCollection,
    path='/scan-jobs',
    converters=dict(
        page=int,
        from_date=extended_date_converter,
        to_date=extended_date_converter,
        type=[str],
        municipality_id=[str],
        sort_by=str,
        sort_order=str
    )
)
def get_scan_jobs(
    request,
    page=None,
    from_date=None,
    to_date=None,
    type=None,
    municipality_id=None,
    term=None,
    sort_by=None,
    sort_order=None
):
    return ScanJobCollection(
        request.session,
        page=page,
        group_id=(
            None if request.has_role('admin')
            else getattr(request.identity, 'groupid', 'nogroup')
        ),
        from_date=from_date,
        to_date=to_date,
        type=type,
        municipality_id=municipality_id,
        term=term,
        sort_by=sort_by,
        sort_order=sort_order
    )


@WtfsApp.path(
    model=ScanJob,
    path='/scan-job/{id}',
    converters=dict(
        id=uuid_converter
    )
)
def get_scan_job(request, id):
    return ScanJobCollection(request.session).by_id(id)


@WtfsApp.path(
    model=DailyList,
    path='/daily-list',
)
def get_daily_list(request):
    return DailyList()


@WtfsApp.path(
    model=DailyListBoxes,
    path='/daily-list/boxes/{date}',
    converters=dict(
        date=extended_date_converter,
    )
)
def get_daily_list_boxes(request, date):
    return DailyListBoxes(request.session, date)


@WtfsApp.path(
    model=DailyListBoxesAndForms,
    path='/daily-list/boxes-and-forms/{date}',
    converters=dict(
        date=extended_date_converter,
    )
)
def get_daily_list_boxes_and_forms(request, date):
    return DailyListBoxesAndForms(request.session, date)


@WtfsApp.path(
    model=Report,
    path='/report',
)
def get_report(request):
    return Report(request.session)


@WtfsApp.path(
    model=ReportBoxes,
    path='/report/boxes/{start}/{end}',
    converters=dict(
        start=extended_date_converter,
        end=extended_date_converter,
    )
)
def get_report_boxes(request, start, end):
    return ReportBoxes(request.session, start, end)


@WtfsApp.path(
    model=ReportBoxesAndForms,
    path='/report/boxes-and-forms/{start}/{end}/{type}',
    converters=dict(
        start=extended_date_converter,
        end=extended_date_converter,
    )
)
def get_report_boxes_and_forms(request, start, end, type):
    return ReportBoxesAndForms(request.session, start, end, type)


@WtfsApp.path(
    model=ReportFormsByMunicipality,
    path='/report/forms/{start}/{end}/{type}/{municipality_id}',
    converters=dict(
        start=extended_date_converter,
        end=extended_date_converter,
        municipality_id=uuid_converter
    )
)
def get_report_forms(request, start, end, type, municipality_id):
    if not municipality_id:
        raise HTTPNotFound()
    return ReportFormsByMunicipality(
        request.session, start, end, type, municipality_id
    )


@WtfsApp.path(
    model=ReportBoxesAndFormsByDelivery,
    path='/report/delivery/{start}/{end}/{type}/{municipality_id}',
    converters=dict(
        start=extended_date_converter,
        end=extended_date_converter,
        municipality_id=uuid_converter
    )
)
def get_report_delivery(request, start, end, type, municipality_id):
    if not municipality_id:
        raise HTTPNotFound()
    return ReportBoxesAndFormsByDelivery(
        request.session, start, end, type, municipality_id
    )


@WtfsApp.path(
    model=NotificationCollection,
    path='/notifications'
)
def get_notifications(request):
    return NotificationCollection(request.session)


@WtfsApp.path(
    model=Notification,
    path='/notification/{id}'
)
def get_notification(request, id):
    return NotificationCollection(request.session).by_id(id)


@WtfsApp.path(
    model=Invoice,
    path='/invoice',
)
def get_invoice(request):
    return Invoice(request.session)


@WtfsApp.path(
    model=PaymentTypeCollection,
    path='/payment-types'
)
def get_payment_types(request):
    return PaymentTypeCollection(request.session)
