from __future__ import annotations

from datetime import date
from onegov.core.elements import Link
from sqlalchemy import exists
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.pas import _
from onegov.org.models import GeneralFileCollection
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import ChangeCollection
from onegov.pas.collections import ImportLogCollection
from onegov.pas.models import Attendence
from onegov.pas.models import SettlementRun, RateSet
from onegov.user import Auth


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.pas.request import PasRequest
    from sqlalchemy.orm import Session


def get_global_tools(request: PasRequest) -> Iterator[Link | LinkGroup]:

    if request.is_logged_in:

        # Logout
        yield LinkGroup(
            request.current_username or _('User'),
            classes=('user',),
            links=(
                Link(
                    _('Logout'), request.link(
                        Auth.from_request(
                            request, to=logout_path(request)), name='logout'
                    ),
                    attrs={'class': 'logout'}
                ),
            )
        )

        # Management Dropdown
        if request.is_admin:
            session = request.session
            management_links: list[Link] = []
            if current_run := get_current_settlement_run(session):
                management_links.append(
                    Link(
                        _('Current Settlement Run'),
                        request.link(current_run),
                        attrs={'class': 'settlement-run'}
                    )
                )

            management_links.extend((
                Link(
                    _('Attendences'),
                    request.class_link(AttendenceCollection),
                    attrs={'class': 'attendances'}
                ),
                Link(
                    _('Changes'),
                    request.class_link(ChangeCollection),
                    attrs={'class': 'changes'}
                ),
                Link(
                    _('Import History'),
                    request.class_link(ImportLogCollection),
                    attrs={'class': 'import-logs'}
                ),
                Link(
                    _('PAS settings'),
                    request.link(request.app.org, 'pas-settings'),
                    attrs={'class': 'pas-settings'}
                ),
                Link(
                    _('Files'),
                    request.link(request.app.org, 'files'),
                    attrs={'class': 'files'}
                ),
                Link(
                    _('More settings'),
                    request.link(request.app.org, 'settings'),
                    attrs={'class': 'settings'}
                ),
                Link(
                    _('User Management'),
                    request.link(request.app.org, 'usermanagement'),
                    attrs={'class': 'usermanagement'}
                ),
            ))

            yield LinkGroup(
                _('Management'), classes=('management',),
                links=management_links
            )

        elif request.is_parliamentarian:
            links = []

            # Add Profile link
            parliamentarian = request.current_user.parliamentarian  # type: ignore[union-attr]
            if parliamentarian:
                profile_url = request.link(parliamentarian)
                if profile_url:
                    links.append(
                        Link(
                            _('Profile'),
                            profile_url,
                            attrs={'class': 'profile'}
                        )
                    )

            links.extend([
                Link(
                    _('Attendences'),
                    request.class_link(AttendenceCollection),
                    attrs={'class': 'attendences'}
                ),
                Link(
                    _('Files'),
                    request.class_link(GeneralFileCollection),
                    attrs={'class': 'files'}
                ),
            ])

            yield LinkGroup(
                _('Management'), classes=('management',),
                links=links
            )


def get_top_navigation(request: PasRequest) -> list[Link]:
    return []


def get_current_settlement_run(session: Session) -> SettlementRun | None:
    today = date.today()
    query = session.query(SettlementRun)
    query = query.filter(
        SettlementRun.start <= today, SettlementRun.end >= today
    )
    # With overlap validation, there can be at most one settlement run
    # containing today's date, so we can safely use first()
    return query.first()


def check_attendance_in_closed_settlement_run(
    session: Session,
    attendance_date: date
) -> bool:
    """ Check if attendance date is in a closed settlement run.

    NOTE: This approach is somewhat not as efficient as it could
    be. A better approach would be:
    - Add settlement_run_id FK to attendances table
    - Direct relationship: attendance.settlement_run
    - No date range queries needed
    We currently have *a lot* of these date range queries
    """
    return session.query(exists().where(
        (SettlementRun.start <= attendance_date) &
        (SettlementRun.end >= attendance_date) &
        (SettlementRun.closed == True)
    )).scalar()


def check_attendance_outside_any_settlement_run(
    session: Session, attendance_date: date
) -> bool:
    """Check if attendance date is outside all settlement runs.

    Returns True if the date is NOT within any settlement run
    (neither open nor closed).
    """
    return not session.query(
        exists().where(
            (SettlementRun.start <= attendance_date)
            & (SettlementRun.end >= attendance_date)
        )
    ).scalar()


def validate_attendance_date(
    session: Session, attendance_date: date
) -> str | None:
    """Validate attendance date for creation/editing.

    Returns error message if invalid, None if valid.
    Checks:
    1. Date is not in a closed settlement run
    2. Date is within some settlement run
    """
    if check_attendance_in_closed_settlement_run(session, attendance_date):
        return _('Cannot create attendance in closed settlement run.')
    if check_attendance_outside_any_settlement_run(session, attendance_date):
        return _('Attendance date must be within a settlement run.')
    return None


def has_user_set_abschluss_for_settlement_run(
    session: Session, parliamentarian_id: str, attendance_date: date
) -> bool:
    """Check if parliamentarian has set abschluss in settlement run.

    Args:
        session: Database session
        parliamentarian_id: UUID of the parliamentarian
        attendance_date: Date to check which settlement run it belongs to

    Returns:
        True if parliamentarian has any attendance with abschluss=True
        in the settlement run containing the given date.
    """
    settlement_run = (
        session.query(SettlementRun)
        .filter(
            SettlementRun.start <= attendance_date,
            SettlementRun.end >= attendance_date,
        )
        .first()
    )

    if not settlement_run:
        return False

    has_abschluss = session.query(
        exists().where(
            (Attendence.parliamentarian_id == parliamentarian_id)
            & (Attendence.date >= settlement_run.start)
            & (Attendence.date <= settlement_run.end)
            & (Attendence.abschluss == True)
        )
    ).scalar()

    return has_abschluss


def get_current_rate_set(session: Session, run: SettlementRun) -> RateSet:
    rat_set = (
        session.query(RateSet).filter(RateSet.year == run.start.year).first()
    )
    # We get the first one we find by year. This works because we are only
    # allowing to create one rate set per year
    if rat_set is None:
        raise ValueError('No rate set found for the current year')
    return rat_set
