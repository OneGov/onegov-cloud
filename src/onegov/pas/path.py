from onegov.pas.app import PasApp
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.models import Commission
from onegov.pas.models import LegislativePeriod
from onegov.pas.models import Parliamentarian
from onegov.pas.models import ParliamentaryGroup
from onegov.pas.models import Party
from uuid import UUID


@PasApp.path(
    model=CommissionCollection,
    path='/commissions'
)
def get_commissions(app: PasApp) -> CommissionCollection:
    return CommissionCollection(app.session())


@PasApp.path(
    model=Commission,
    path='/commission/{id}',
    converters={'id': UUID}
)
def get_commission(app: PasApp, id: UUID) -> Commission | None:
    return CommissionCollection(app.session()).by_id(id)


@PasApp.path(
    model=LegislativePeriodCollection,
    path='/legislative-periods'
)
def get_legislative_periods(app: PasApp) -> LegislativePeriodCollection:
    return LegislativePeriodCollection(app.session())


@PasApp.path(
    model=LegislativePeriod,
    path='/legislative-period/{id}',
    converters={'id': UUID}
)
def get_legislative_period(app: PasApp, id: UUID) -> LegislativePeriod | None:
    return LegislativePeriodCollection(app.session()).by_id(id)


@PasApp.path(
    model=ParliamentarianCollection,
    path='/parliamenarians'
)
def get_parliamentarians(app: PasApp) -> ParliamentarianCollection:
    return ParliamentarianCollection(app.session())


@PasApp.path(
    model=Parliamentarian,
    path='/parliamenarian/{id}',
    converters={'id': UUID}
)
def get_parliamentarian(app: PasApp, id: UUID) -> Parliamentarian | None:
    return ParliamentarianCollection(app.session()).by_id(id)


@PasApp.path(
    model=ParliamentaryGroupCollection,
    path='/parliamenary-groups'
)
def get_parliamentary_groups(app: PasApp) -> ParliamentaryGroupCollection:
    return ParliamentaryGroupCollection(app.session())


@PasApp.path(
    model=ParliamentaryGroup,
    path='/parliamenary-group/{id}',
    converters={'id': UUID}
)
def get_parliamentary_group(
    app: PasApp,
    id: UUID
) -> ParliamentaryGroup | None:
    return ParliamentaryGroupCollection(app.session()).by_id(id)


@PasApp.path(
    model=PartyCollection,
    path='/parties'
)
def get_parties(app: PasApp) -> PartyCollection:
    return PartyCollection(app.session())


@PasApp.path(
    model=Party,
    path='/party/{id}',
    converters={'id': UUID}
)
def get_party(app: PasApp, id: UUID) -> Party | None:
    return PartyCollection(app.session()).by_id(id)
