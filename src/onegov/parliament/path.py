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
from onegov.parliament.collections import RISParliamentarianCollection
from onegov.parliament.collections import (
    RISParliamentaryGroupCollection
)
from onegov.parliament.models import (
    Commission,
    Meeting,
    ParliamentaryGroup,
    Party,
    RISCommission,
    RISParliamentarian,
    RISParliamentaryGroup,
    RISParty,
)
from onegov.town6.app import TownApp


@TownApp.path(
    model=RISParliamentarianCollection,
    path='/parliamentarians',
    converters={'active': bool}
)
def get_parliamentarians(
    app: TownApp,
    active: bool = True
) -> RISParliamentarianCollection:
    return RISParliamentarianCollection(app.session(), active)


@TownApp.path(
    model=RISParliamentarian,
    path='/parliamentarian/{id}',
    converters={'id': UUID}
)
def get_parliamentarian(
    app: TownApp,
    id: UUID
) -> RISParliamentarian | None:
    return RISParliamentarianCollection(app.session()).by_id(id)


# @TownApp.path(
#     model=RISParliamentarianRoleCollection,
#     path='/parliamentarian-roles',
# )
# def get_parliamentarian_roles(
#     app: TownApp,
# ) -> RISParliamentarianRoleCollection:
#     return RISParliamentarianRoleCollection(app.session())
#
#
# @TownApp.path(
#     model=RISParliamentarianRole,
#     path='/parliamentarian-role/{id}',
#     converters={'id': UUID}
# )
# def get_parliamentarian_role(
#     app: TownApp,
#     id: UUID
# ) -> RISParliamentarianRole | None:
#     return RISParliamentarianCollection(app.session()).by_id(id)


@TownApp.path(
    model=RISParliamentaryGroupCollection,
    path='/parliamentary-groups',
    converters={'active': bool}
)
def get_parliamentary_groups(
    app: TownApp,
    active: bool = True
) -> RISParliamentaryGroupCollection:
    return RISParliamentaryGroupCollection(app.session(), active)


@TownApp.path(
    model=RISParliamentaryGroup,
    path='/parliamentary-group/{id}',
    converters={'id': UUID}
)
def get_parliamentary_group(
    app: TownApp,
    id: UUID
) -> ParliamentaryGroup | None:
    return RISParliamentaryGroupCollection(app.session()).by_id(id)


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
    return RISCommissionCollection(app.session(), active)


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
