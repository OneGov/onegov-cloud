from __future__ import annotations
from collections import defaultdict
from io import BytesIO
from decimal import Decimal
import xlsxwriter   # type: ignore[import-untyped]

from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import (
    AttendenceCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.utils import (
    get_parliamentarians_with_settlements,
)

from onegov.pas.models.settlement_run import SettlementRun


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.request import TownRequest

# these are the two last exports from email
# We are writing the abschlussliste export,


def get_abschlussliste_data(
    settlement_run: SettlementRun,
    request: TownRequest,
) -> list[dict[str, Any]]:
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)
    if not rate_set:
        return []

    parliamentarians = get_parliamentarians_with_settlements(
        session, settlement_run.start, settlement_run.end
    )

    parl_data: defaultdict[str, dict[str, Any]] = defaultdict(
        lambda: {
            'plenum_duration': Decimal('0'),
            'plenum_compensation': Decimal('0'),
            'commission_duration': Decimal('0'),
            'commission_compensation': Decimal('0'),
            'study_duration': Decimal('0'),
            'study_compensation': Decimal('0'),
            'shortest_duration': Decimal('0'),
            'shortest_compensation': Decimal('0'),
            'expenses': Decimal('0'),
        }
    )

    attendances = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end,
    ).query()

    for att in attendances:
        p = att.parliamentarian
        is_president = any(r.role == 'president' for r in p.roles)
        compensation = calculate_rate(
            rate_set=rate_set,
            attendence_type=att.type,
            duration_minutes=int(att.duration),
            is_president=is_president,
            commission_type=att.commission.type if att.commission else None
        )

        data = parl_data[str(p.id)]
        if att.type == 'plenary':
            data['plenum_duration'] += Decimal(att.duration)
            data['plenum_compensation'] += Decimal(str(compensation))
        elif att.type == 'commission':
            data['commission_duration'] += Decimal(att.duration)
            data['commission_compensation'] += Decimal(str(compensation))
        elif att.type == 'study':
            data['study_duration'] += Decimal(att.duration)
            data['study_compensation'] += Decimal(str(compensation))
        elif att.type == 'shortest':
            data['shortest_duration'] += Decimal(att.duration)
            data['shortest_compensation'] += Decimal(str(compensation))

    result = []
    for p in parliamentarians:
        party = p.get_party_during_period(
            settlement_run.start, settlement_run.end, session
        )
        data = parl_data[str(p.id)]
        data['parliamentarian'] = p
        data['party'] = party.name if party else ''
        data['faction'] = party.name if party else ''
        result.append(data)

    return sorted(
        result,
        key=lambda x: (
            x['parliamentarian'].last_name,
            x['parliamentarian'].first_name
        )
    )


def generate_abschlussliste_xlsx(
    settlement_run: SettlementRun,
    request: TownRequest
) -> BytesIO:
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # Details tab
    details_ws = workbook.add_worksheet('Details')
    details_headers = [
        'Name', 'Vorname', 'Partei', 'Fraktion',
        'Plenum / Kommission Zeit', 'Entschädigung',
        'Aktenstudium Zeit', 'Aktenstudium Entschädigung',
        'Kürzestsitzungen Zeit', 'Kürzestsitzungen Entschädigung'
    ]
    details_ws.write_row(0, 0, details_headers)

    # Übersicht tab
    overview_ws = workbook.add_worksheet('Übersicht')
    overview_headers = [
        'Name', 'Vorname', 'Partei', 'Fraktion',
        'Plenum Zeit', 'Plenum Entschädigung',
        'Kommissionen Zeit', 'Kommissionen Entschädigung',
        'Spesen'
    ]
    overview_ws.write_row(0, 0, overview_headers)

    data = get_abschlussliste_data(settlement_run, request)

    for row_num, row_data in enumerate(data, 1):
        p = row_data['parliamentarian']

        # Details tab row
        details_row = [
            p.last_name, p.first_name, row_data['party'], row_data['faction'],
            row_data['plenum_duration'] + row_data['commission_duration'],
            row_data['plenum_compensation']
            + row_data['commission_compensation'],
            row_data['study_duration'], row_data['study_compensation'],
            row_data['shortest_duration'], row_data['shortest_compensation']
        ]
        details_ws.write_row(row_num, 0, details_row)

        # Übersicht tab row
        overview_row = [
            p.last_name, p.first_name, row_data['party'], row_data['faction'],
            row_data['plenum_duration'], row_data['plenum_compensation'],
            row_data['commission_duration'] + row_data['shortest_duration'],
            row_data['commission_compensation']
            + row_data['shortest_compensation'],
            row_data['expenses']
        ]
        overview_ws.write_row(row_num, 0, overview_row)

    workbook.close()
    output.seek(0)
    return output
