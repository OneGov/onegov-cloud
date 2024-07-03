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
from onegov.wtfs.models import ReportFormsAllMunicipalities
from onegov.wtfs.models import ReportFormsByMunicipality
from onegov.wtfs.models import ScanJob
from onegov.wtfs.models import UserManual
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.core.request import CoreRequest
    from uuid import UUID


@WtfsApp.path(
    model=Principal,
    path='/'
)
def get_principal(app: WtfsApp) -> Principal:
    return app.principal


@WtfsApp.path(
    model=Auth,
    path='/auth'
)
def get_auth(request: 'CoreRequest', to: str = '/') -> Auth:
    return Auth.from_request(request, to)


@WtfsApp.path(
    model=UserCollection,
    path='/users'
)
def get_users(request: 'CoreRequest') -> UserCollection:
    return UserCollection(request.session)


@WtfsApp.path(
    model=User,
    path='/user/{username}'
)
def get_user(request: 'CoreRequest', username: str) -> User | None:
    return UserCollection(request.session).by_username(username)


@WtfsApp.path(
    model=MunicipalityCollection,
    path='/municipalities'
)
def get_municipalities(request: 'CoreRequest') -> MunicipalityCollection:
    return MunicipalityCollection(request.session)


@WtfsApp.path(
    model=Municipality,
    path='/municipality/{id}',
    converters={
        'id': uuid_converter
    }
)
def get_municipality(
    request: 'CoreRequest',
    id: 'UUID'
) -> Municipality | None:
    return MunicipalityCollection(request.session).by_id(id)


@WtfsApp.path(
    model=ScanJobCollection,
    path='/scan-jobs',
    converters={
        'page': int,
        'from_date': extended_date_converter,
        'to_date': extended_date_converter,
        'type': [str],
        'municipality_id': [str],
        'sort_by': str,
        'sort_order': str
    }
)
def get_scan_jobs(
    request: 'CoreRequest',
    page: int = 0,
    from_date: 'date | None' = None,
    to_date: 'date | None' = None,
    type: list[str] | None = None,
    municipality_id: list[str] | None = None,
    term: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None
) -> ScanJobCollection:
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
    converters={
        'id': uuid_converter
    }
)
def get_scan_job(request: 'CoreRequest', id: 'UUID') -> ScanJob | None:
    return ScanJobCollection(request.session).by_id(id)


@WtfsApp.path(
    model=DailyList,
    path='/daily-list',
)
def get_daily_list(request: 'CoreRequest') -> DailyList:
    return DailyList()


@WtfsApp.path(
    model=DailyListBoxes,
    path='/daily-list/boxes/{date}',
    converters={
        'date': extended_date_converter,
    }
)
def get_daily_list_boxes(
    request: 'CoreRequest',
    date: 'date'
) -> DailyListBoxes:
    return DailyListBoxes(request.session, date)


@WtfsApp.path(
    model=DailyListBoxesAndForms,
    path='/daily-list/boxes-and-forms/{date}',
    converters={
        'date': extended_date_converter,
    }
)
def get_daily_list_boxes_and_forms(
    request: 'CoreRequest',
    date: 'date'
) -> DailyListBoxesAndForms:
    return DailyListBoxesAndForms(request.session, date)


@WtfsApp.path(
    model=Report,
    path='/report',
)
def get_report(request: 'CoreRequest') -> Report:
    return Report(request.session)


@WtfsApp.path(
    model=ReportBoxes,
    path='/report/boxes/{start}/{end}',
    converters={
        'start': extended_date_converter,
        'end': extended_date_converter,
    }
)
def get_report_boxes(
    request: 'CoreRequest',
    start: 'date',
    end: 'date'
) -> ReportBoxes:
    return ReportBoxes(request.session, start, end)


@WtfsApp.path(
    model=ReportBoxesAndForms,
    path='/report/boxes-and-forms/{start}/{end}/{type}',
    converters={
        'start': extended_date_converter,
        'end': extended_date_converter,
    }
)
def get_report_boxes_and_forms(
    request: 'CoreRequest',
    start: 'date',
    end: 'date',
    type: str
) -> ReportBoxesAndForms:
    return ReportBoxesAndForms(request.session, start, end, type)


@WtfsApp.path(
    model=ReportFormsAllMunicipalities,
    path='/report/all-forms/{start}/{end}/{type}',
    converters={
        'start': extended_date_converter,
        'end': extended_date_converter,
    }
)
def get_report_all_forms(
    request: 'CoreRequest',
    start: 'date',
    end: 'date',
    type: str
) -> ReportFormsAllMunicipalities:
    return ReportFormsAllMunicipalities(request.session, start, end, type)


@WtfsApp.path(
    model=ReportFormsByMunicipality,
    path='/report/forms/{start}/{end}/{type}/{municipality_id}',
    converters={
        'start': extended_date_converter,
        'end': extended_date_converter,
        'municipality_id': uuid_converter
    }
)
def get_report_forms(
    request: 'CoreRequest',
    start: 'date',
    end: 'date',
    type: str,
    municipality_id: 'UUID | None'
) -> ReportFormsByMunicipality:
    if not municipality_id:
        raise HTTPNotFound()
    return ReportFormsByMunicipality(
        request.session, start, end, type, municipality_id
    )


@WtfsApp.path(
    model=ReportBoxesAndFormsByDelivery,
    path='/report/delivery/{start}/{end}/{type}/{municipality_id}',
    converters={
        'start': extended_date_converter,
        'end': extended_date_converter,
        'municipality_id': uuid_converter
    }
)
def get_report_delivery(
    request: 'CoreRequest',
    start: 'date',
    end: 'date',
    type: str,
    municipality_id: 'UUID | None'
) -> ReportBoxesAndFormsByDelivery:
    if not municipality_id:
        raise HTTPNotFound()
    return ReportBoxesAndFormsByDelivery(
        request.session, start, end, type, municipality_id
    )


@WtfsApp.path(
    model=NotificationCollection,
    path='/notifications'
)
def get_notifications(request: 'CoreRequest') -> NotificationCollection:
    return NotificationCollection(request.session)


@WtfsApp.path(
    model=Notification,
    path='/notification/{id}'
)
def get_notification(request: 'CoreRequest', id: str) -> Notification | None:
    return NotificationCollection(request.session).by_id(id)


@WtfsApp.path(
    model=Invoice,
    path='/invoice',
)
def get_invoice(request: 'CoreRequest') -> Invoice:
    return Invoice(request.session)


@WtfsApp.path(
    model=PaymentTypeCollection,
    path='/payment-types'
)
def get_payment_types(request: 'CoreRequest') -> PaymentTypeCollection:
    return PaymentTypeCollection(request.session)


@WtfsApp.path(
    model=UserManual,
    path='/user-manual',
)
def get_user_manual(request: 'CoreRequest') -> UserManual:
    return UserManual(request.app)  # type:ignore[arg-type]
