from __future__ import annotations

from onegov.pas.utils import is_parliamentarian_role
from onegov.core.elements import Link
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.pas import _
from onegov.org.models import GeneralFileCollection
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import ChangeCollection
from onegov.pas.collections import PASCommissionCollection
from onegov.user import Auth
from onegov.user import UserCollection
from onegov.pas.models import SettlementRun, RateSet

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
            yield LinkGroup(
                _('Management'), classes=('management',),
                links=(
                    Link(
                        _('Attendences'),
                        request.class_link(AttendenceCollection),
                        attrs={'class': 'attendences'}
                    ),
                    Link(
                        _('Changes'),
                        request.class_link(ChangeCollection),
                        attrs={'class': 'changes'}
                    ),
                    Link(
                        _('Files'),
                        request.class_link(GeneralFileCollection),
                        attrs={'class': 'files'}
                    ),
                    Link(
                        _('PAS settings'),
                        request.link(request.app.org, 'pas-settings'),
                        attrs={'class': 'pas-settings'}
                    ),
                    Link(
                        _('More settings'),
                        request.link(request.app.org, 'settings'),
                        attrs={'class': 'settings'}
                    ),
                    Link(
                        _('Users'), request.class_link(UserCollection),
                        attrs={'class': 'user'}
                    ),
                )
            )
        elif (request.is_logged_in
              and hasattr(request.identity, 'role')
              and is_parliamentarian_role(request.identity.role)):
            yield LinkGroup(
                _('Management'), classes=('management',),
                links=(
                    Link(
                        _('Attendences'),
                        request.class_link(AttendenceCollection),
                        attrs={'class': 'attendences'}
                    ),
                    Link(
                        _('Commissions'),
                        request.class_link(PASCommissionCollection),
                        attrs={'class': 'commissions'}
                    ),
                    Link(
                        _('Files'),
                        request.class_link(GeneralFileCollection),
                        attrs={'class': 'files'}
                    ),
                )
            )


def get_top_navigation(request: TownRequest) -> list[Link]:
    return []


def get_current_settlement_run(session: Session) -> SettlementRun:
    query = session.query(SettlementRun)
    query = query.filter(SettlementRun.active == True)
    return query.one()


def get_current_rate_set(session: Session, run: SettlementRun) -> RateSet:
    rat_set = (
        session.query(RateSet).filter(RateSet.year == run.start.year).first()
    )
    # We get the first one we find by year. This works because we are only
    # allowing to create one rate set per year
    if rat_set is None:
        raise ValueError('No rate set found for the current year')
    return rat_set
