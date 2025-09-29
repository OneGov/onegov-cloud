from __future__ import annotations

from onegov.core.elements import Link
from sqlalchemy import exists
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.pas import _
from onegov.org.models import GeneralFileCollection
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import ChangeCollection
from onegov.pas.collections import ImportLogCollection
from onegov.user import Auth
from onegov.pas.models import SettlementRun, RateSet
from sqlalchemy.orm.exc import MultipleResultsFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.pas.request import PasRequest
    from datetime import date
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
    query = session.query(SettlementRun)
    query = query.filter(SettlementRun.active.is_(True))
    try:
        return query.one_or_none()
    except MultipleResultsFound:
        # If multiple active runs exist (happens in testing)
        # The caller must handle the None case
        return None


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


def get_current_rate_set(session: Session, run: SettlementRun) -> RateSet:
    rat_set = (
        session.query(RateSet).filter(RateSet.year == run.start.year).first()
    )
    # We get the first one we find by year. This works because we are only
    # allowing to create one rate set per year
    if rat_set is None:
        raise ValueError('No rate set found for the current year')
    return rat_set
