from __future__ import annotations

from onegov.core.elements import Link
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections import AttendanceCollection
from onegov.pas.collections import ChangeCollection
from onegov.user import Auth
from onegov.pas.models import SettlementRun, RateSet
from sqlalchemy.orm.exc import MultipleResultsFound

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.town6.request import TownRequest
    from sqlalchemy.orm import Session


def get_global_tools(request: TownRequest) -> Iterator[Link | LinkGroup]:

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
            try:
                current_run = get_current_settlement_run(session)
                if current_run:
                    management_links.append(
                        Link(
                            _('Current Settlement Run'),
                            request.link(current_run),
                            attrs={'class': 'settlement-run'}
                        )
                    )
            except MultipleResultsFound:
                # If multiple active runs exist (should not happen), but
                # just to # be safe
                pass

            management_links.extend((
                Link(
                    _('Attendances'),
                    request.class_link(AttendanceCollection),
                    attrs={'class': 'attendances'}
                ),
                Link(
                    _('Changes'),
                    request.class_link(ChangeCollection),
                    attrs={'class': 'changes'}
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
            ))

            yield LinkGroup(
                _('Management'),
                classes=('management',),
                links=tuple(management_links)
            )


def get_top_navigation(request: TownRequest) -> list[Link]:
    return []


def get_current_settlement_run(session: Session) -> SettlementRun | None:
    query = session.query(SettlementRun)
    query = query.filter(SettlementRun.active == True)
    return query.first()


def get_current_rate_set(session: Session, run: SettlementRun) -> RateSet:
    rat_set = (
        session.query(RateSet).filter(RateSet.year == run.start.year).first()
    )
    # We get the first one we find by year. This works because we are only
    # allowing to create one rate set per year
    if rat_set is None:
        raise ValueError('No rate set found for the current year')
    return rat_set
