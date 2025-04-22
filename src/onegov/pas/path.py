from __future__ import annotations

from onegov.pas.collections import AttendenceCollection
from onegov.pas.app import PasApp
from onegov.pas.collections import ChangeCollection
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import CommissionMembershipCollection
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.collections import ParliamentarianRoleCollection
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.collections import RateSetCollection
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.collections import ImportLogCollection
from onegov.pas.models import Attendence
from onegov.pas.models import Change
from onegov.pas.models import Commission
from onegov.pas.models import CommissionMembership
from onegov.pas.models import ImportLog
from onegov.pas.models import LegislativePeriod
from onegov.pas.models import Parliamentarian
from onegov.pas.models import ParliamentarianRole
from onegov.pas.models import ParliamentaryGroup
from onegov.pas.models import Party
from onegov.pas.models import RateSet
from onegov.pas.models import SettlementRun
from uuid import UUID
from datetime import date


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.request import TownRequest


@PasApp.path(
    model=AttendenceCollection,
    path='/attendences',
    converters={
        'page': int,
        'settlement_run_id': str,
        'date_from': date,
        'date_to': date,
        'type': str,
        'parliamentarian_id': str,
        'commission_id': str
    }
)
def get_attendences(
    request: TownRequest,
    settlement_run_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    type: str | None = None,
    parliamentarian_id: str | None = None,
    commission_id: str | None = None
) -> AttendenceCollection:
    return AttendenceCollection(
        session=request.session,
        settlement_run_id=settlement_run_id,
        date_from=date_from,
        date_to=date_to,
        type=type,
        parliamentarian_id=parliamentarian_id,
        commission_id=commission_id
    )


@PasApp.path(
    model=Attendence,
    path='/attendence/{id}',
    converters={'id': UUID}
)
def get_attendence(
    app: PasApp,
    id: UUID
) -> Attendence | None:
    return AttendenceCollection(app.session()).by_id(id)


@PasApp.path(
    model=ChangeCollection,
    path='/changes'
)
def get_changes(
    app: PasApp
) -> ChangeCollection:
    return ChangeCollection(app.session())


@PasApp.path(
    model=Change,
    path='/change/{id}',
    converters={'id': UUID}
)
def get_change(
    app: PasApp,
    id: UUID
) -> Change | None:
    return ChangeCollection(app.session()).by_id(id)


@PasApp.path(
    model=CommissionCollection,
    path='/commissions',
    converters={'active': bool}
)
def get_commissions(
    app: PasApp,
    active: bool = True
) -> CommissionCollection:
    return CommissionCollection(app.session(), active)


@PasApp.path(
    model=Commission,
    path='/commission/{id}',
    converters={'id': UUID}
)
def get_commission(
    app: PasApp,
    id: UUID,
) -> Commission | None:
    return CommissionCollection(app.session()).by_id(id)


@PasApp.path(
    model=CommissionMembershipCollection,
    path='/commission-memberships'
)
def get_commission_memberships(
    app: PasApp
) -> CommissionMembershipCollection:
    return CommissionMembershipCollection(app.session())


@PasApp.path(
    model=CommissionMembership,
    path='/commission-membership/{id}',
    converters={'id': UUID}
)
def get_commission_membership(
    app: PasApp,
    id: UUID
) -> CommissionMembership | None:
    return CommissionMembershipCollection(app.session()).by_id(id)


@PasApp.path(
    model=LegislativePeriodCollection,
    path='/legislative-periods',
    converters={'active': bool}
)
def get_legislative_periods(
    app: PasApp,
    active: bool = True
) -> LegislativePeriodCollection:
    return LegislativePeriodCollection(app.session(), active)


@PasApp.path(
    model=LegislativePeriod,
    path='/legislative-period/{id}',
    converters={'id': UUID}
)
def get_legislative_period(
    app: PasApp,
    id: UUID
) -> LegislativePeriod | None:
    return LegislativePeriodCollection(app.session()).by_id(id)


@PasApp.path(
    model=ParliamentarianCollection,
    path='/parliamenarians',
    converters={'active': bool}
)
def get_parliamentarians(
    app: PasApp,
    active: bool = True
) -> ParliamentarianCollection:
    return ParliamentarianCollection(app.session(), active)


@PasApp.path(
    model=Parliamentarian,
    path='/parliamenarian/{id}',
    converters={'id': UUID}
)
def get_parliamentarian(
    app: PasApp,
    id: UUID
) -> Parliamentarian | None:
    return ParliamentarianCollection(app.session()).by_id(id)


@PasApp.path(
    model=ParliamentarianRoleCollection,
    path='/parliamenarian-roles'
)
def get_parliamentarian_roles(
    app: PasApp
) -> ParliamentarianRoleCollection:
    return ParliamentarianRoleCollection(app.session())


@PasApp.path(
    model=ParliamentarianRole,
    path='/parliamenarian-role/{id}',
    converters={'id': UUID}
)
def get_parliamentarian_role(
    app: PasApp,
    id: UUID
) -> ParliamentarianRole | None:
    return ParliamentarianRoleCollection(app.session()).by_id(id)


@PasApp.path(
    model=ParliamentaryGroupCollection,
    path='/parliamenary-groups',
    converters={'active': bool}
)
def get_parliamentary_groups(
    app: PasApp,
    active: bool = True,
) -> ParliamentaryGroupCollection:
    return ParliamentaryGroupCollection(app.session(), active)


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
    path='/parties',
    converters={'active': bool}
)
def get_parties(
    app: PasApp,
    active: bool = True,
) -> PartyCollection:
    return PartyCollection(app.session(), active)


@PasApp.path(
    model=Party,
    path='/party/{id}',
    converters={'id': UUID}
)
def get_party(
    app: PasApp,
    id: UUID
) -> Party | None:
    return PartyCollection(app.session()).by_id(id)


@PasApp.path(
    model=RateSetCollection,
    path='/rate-sets',
    converters={'active': bool}
)
def get_rate_sets(
    app: PasApp,
    active: bool = True,
) -> RateSetCollection:
    return RateSetCollection(app.session(), active)


@PasApp.path(
    model=RateSet,
    path='/rate-set/{id}',
    converters={'id': UUID}
)
def get_rate_set(
    app: PasApp,
    id: UUID
) -> RateSet | None:
    return RateSetCollection(app.session()).by_id(id)


@PasApp.path(
    model=SettlementRunCollection,
    path='/settlement-runs',
    converters={'active': bool}
)
def get_settlement_runs(
    app: PasApp,
    active: bool = True,
) -> SettlementRunCollection:
    return SettlementRunCollection(app.session(), active)


@PasApp.path(
    model=SettlementRun,
    path='/settlement-run/{id}',
    converters={'id': UUID}
)
def get_settlement_run(
    app: PasApp,
    id: UUID
) -> SettlementRun | None:
    return SettlementRunCollection(app.session()).by_id(id)


class SettlementRunExport:
    """ Tiny wrapper class for easing the morepath Path Linking
    (Acts as a container to pass multiple models in the morepath link.)

    """

    def __init__(
        self,
        settlement_run: SettlementRun,
        entity: Party | Commission | Parliamentarian,
        category: str | None = None
    ):
        self.settlement_run = settlement_run
        self.entity = entity
        self.category = category
        self.id = settlement_run.id
        self.entity_id = entity.id
        self.literal_type = type(entity).__name__


class SettlementRunAllExport:
    """Special model for 'all' exports without entity """
    def __init__(
        self,
        settlement_run: SettlementRun,
        category: str,
    ):
        self.settlement_run = settlement_run
        self.category = category
        self.id = settlement_run.id


@PasApp.path(
    model=SettlementRunExport,
    path='/run-export/{id}/{category}/{entity_id}',
    converters={'id': UUID, 'entity_id': UUID},
)
def get_settlement_run_export(
    request: TownRequest,
    id: UUID,
    category: str,
    entity_id: UUID,
    literal_type: str,
) -> SettlementRunExport | None:
    session = request.session
    settlement_run = session.query(SettlementRun).filter_by(id=id).first()
    if not settlement_run:
        return None

    model_map: dict[str, type] = {
        'Party': Party,
        'Commission': Commission,
        'Parliamentarian': Parliamentarian,
    }
    entity = (
        session.query(model_map.get(literal_type))
        .filter_by(id=entity_id)
        .first()
    )
    if not entity:
        return None

    return SettlementRunExport(
        settlement_run=settlement_run, entity=entity, category=category
    )


@PasApp.path(
    model=SettlementRunAllExport,
    path='/run-export/{id}/all/{category}',
    converters={'id': UUID}
)
def get_settlement_run_export_all(
    request: TownRequest,
    id: UUID,
    category: str
) -> SettlementRunAllExport | None:
    """Path for 'all' exports without specific entity"""
    session = request.session
    settlement_run = session.query(SettlementRun).filter_by(id=id).first()
    if not settlement_run:
        return None

    return SettlementRunAllExport(
        settlement_run=settlement_run,
        category=category
    )


@PasApp.path(
    model=ImportLogCollection,
    path='/import-logs'
)
def get_import_logs(
    request: TownRequest
) -> ImportLogCollection:
    """ Returns the collection of import logs. """
    return ImportLogCollection(request.session)


@PasApp.path(
    model=ImportLog,
    path='/import-log/{id}',
    converters={'id': UUID}
)
def get_import_log(
    request: TownRequest,
    id: UUID
) -> ImportLog | None:
    """ Returns a single import log by id. """
    return ImportLogCollection(request.session).by_id(id)
