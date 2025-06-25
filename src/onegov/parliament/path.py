from __future__ import annotations
from uuid import UUID

from onegov.parliament.collections import (
    RISPartyCollection,
    MeetingCollection
)
from onegov.parliament.collections.commission import (
    CommissionCollection,
    RISCommissionCollection
)
from onegov.parliament.models import RISParty, Party, RISCommission, Commission
from onegov.parliament.models.meeting import Meeting
from onegov.town6.app import TownApp


@TownApp.path(
    model=RISPartyCollection,
    path='/parties',
    converters={'active': bool}
)
def get_parties(
    app: TownApp,
    active: bool = True,
) -> RISPartyCollection:
    return RISPartyCollection(app.session(), active)


@TownApp.path(
    model=RISParty,
    path='/party/{id}',
    converters={'id': UUID}
)
def get_party(
    app: TownApp,
    id: UUID
) -> Party | None:
    return RISPartyCollection(app.session()).by_id(id)


@TownApp.path(
    model=CommissionCollection,
    path='/commissions',
    converters={'active': bool}
)
def get_commissions(
    app: TownApp,
    active: bool = True
) -> CommissionCollection:
    return RISCommissionCollection(app.session(), active=active)


@TownApp.path(
    model=RISCommission,
    path='/commission/{id}',
    converters={'id': UUID}
)
def get_commission(
    app: TownApp,
    id: UUID
) -> Commission | None:
    return RISCommissionCollection(app.session()).by_id(id)


@TownApp.path(
    model=MeetingCollection,
    path='/meetings',
)
def get_meetings(
    app: TownApp,
) -> MeetingCollection:
    return MeetingCollection(app.session())


@TownApp.path(
    model=Meeting,
    path='/meeting/{id}',
    converters={'id': UUID}
)
def get_meeting(
    app: TownApp,
    id: UUID
) -> Meeting | None:
    return MeetingCollection(app.session()).by_id(id)
