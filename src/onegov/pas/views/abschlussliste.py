from __future__ import annotations
from collections import defaultdict
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from operator import itemgetter
import xlsxwriter

from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import (
    AttendenceCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.utils import (
    get_parliamentarians_with_settlements,
    is_commission_president,
)
from onegov.pas.models.parliamentarian_role import PASParliamentarianRole
from onegov.pas.models.party import Party
from sqlalchemy import or_

from onegov.pas.models.attendence import TYPES


from typing import Any, TypedDict, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.town6.request import TownRequest
    from onegov.pas.models.settlement_run import SettlementRun
    from sqlalchemy.orm import Session


class BookingRowData(TypedDict):
    date: date
    person: str
    party: str
    wahlkreis: str
    booking_type: str
    value: Decimal
    chf: Decimal
    chf_with_cola: Decimal


def get_party_lookup(
    session: Session,
    parliamentarian_ids: set[str],
    start_date: date,
    end_date: date
) -> dict[str, Party | None]:
    """
    Bulk fetch party information for parliamentarians during a period.
    Returns a lookup dictionary to avoid N+1 queries.
    """
    # Fetch all relevant roles in one query
    roles = (
        session.query(PASParliamentarianRole)
        .join(Party)
        .filter(
            PASParliamentarianRole.parliamentarian_id.in_(parliamentarian_ids),
            PASParliamentarianRole.party_id.isnot(None),
            or_(
                PASParliamentarianRole.end.is_(None),
                PASParliamentarianRole.end >= start_date,
            ),
            PASParliamentarianRole.start <= end_date,
        )
        .order_by(PASParliamentarianRole.start.desc())
        .all()
    )

    # Build lookup dictionary - take the most recent role for each parl
    party_lookup: dict[str, Party | None] = {}
    for parliamentarian_id in parliamentarian_ids:
        party_lookup[parliamentarian_id] = None
    for role in roles:
        parl_id = str(role.parliamentarian_id)
        if parl_id not in party_lookup or party_lookup[parl_id] is None:
            party_lookup[parl_id] = role.party
    return party_lookup


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

    # Get bulk party lookup to avoid N+1 queries
    parliamentarian_ids = {str(p.id) for p in parliamentarians}
    party_lookup = get_party_lookup(
        session, parliamentarian_ids, settlement_run.start, settlement_run.end
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

    # Use optimized query with eager loading
    attendances = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end,
    ).query()

    for att in attendances:
        p = att.parliamentarian
        is_president = is_commission_president(p, att, settlement_run)
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
        party = party_lookup[str(p.id)]
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

    # Define formats
    header_format = workbook.add_format({
        'font_name': 'Arial',
        'font_size': 11,
        'bold': True
    })
    cell_format = workbook.add_format({
        'font_name': 'Arial',
        'font_size': 11
    })

    # Übersicht tab
    overview_ws = workbook.add_worksheet('Übersicht')
    overview_headers = [
        'Name', 'Vorname', 'Partei', 'Fraktion',
        'Plenum Zeit', 'Plenum Entschädigung',
        'Kommissionen Zeit', 'Kommissionen Entschädigung',
        'Spesen'
    ]
    for col, header in enumerate(overview_headers):
        overview_ws.write(0, col, header, header_format)

    # Details tab - individual attendance records
    details_ws = workbook.add_worksheet('Details')
    details_headers = [
        'Datum', 'Name', 'Vorname', 'Partei', 'Fraktion',
        'Typ', 'Kommission', 'Zeit', 'Entschädigung'
    ]
    for col, header in enumerate(details_headers):
        details_ws.write(0, col, header, header_format)

    # Get aggregated data for Übersicht tab
    data = get_abschlussliste_data(settlement_run, request)

    # Get individual attendance records for Details tab
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)
    attendances = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end,
    ).query().all()

    # Get bulk party lookup for details
    attendance_parliamentarian_ids = {
        str(att.parliamentarian.id) for att in attendances
    }
    details_party_lookup = get_party_lookup(
        session,
        attendance_parliamentarian_ids,
        settlement_run.start,
        settlement_run.end
    )

    # Write Details tab with individual attendance records
    for details_row_num, att in enumerate(attendances, start=1):
        p = att.parliamentarian
        party = details_party_lookup[str(p.id)]
        is_president = is_commission_president(p, att, settlement_run)
        compensation = calculate_rate(
            rate_set=rate_set,
            attendence_type=att.type,
            duration_minutes=int(att.duration),
            is_president=is_president,
            commission_type=att.commission.type if att.commission else None
        )

        details_row = [
            att.date.strftime('%d.%m.%Y'),
            p.last_name,
            p.first_name,
            party.name if party else '',
            party.name if party else '',  # faction same as party
            request.translate(TYPES[att.type]),
            att.commission.name if att.commission else '',
            att.calculate_value(),
            compensation
        ]
        for col, value in enumerate(details_row):
            details_ws.write(details_row_num, col, value, cell_format)

    # Write Übersicht tab with aggregated data
    for row_num, row_data in enumerate(data, 1):
        p = row_data['parliamentarian']

        # Übersicht tab row
        overview_row = [
            p.last_name, p.first_name, row_data['party'], row_data['faction'],
            row_data['plenum_duration'], row_data['plenum_compensation'],
            row_data['commission_duration'] + row_data['shortest_duration'],
            row_data['commission_compensation']
            + row_data['shortest_compensation'],
            row_data['expenses']
        ]
        for col, value in enumerate(overview_row):
            overview_ws.write(row_num, col, value, cell_format)

    workbook.close()
    output.seek(0)
    return output


def generate_buchungen_abrechnungslauf_xlsx(
    settlement_run: SettlementRun,
    request: TownRequest
) -> BytesIO:
    """Generate XLSX export for 'Buchungen Abrechnungslauf' with individual
    booking entries.

    Creates an Excel file with columns:
    - Datum: Date of attendance
    - Person: Full name of parliamentarian
    - Partei: Party name
    - Wahlkreis: Electoral district (TODO: determine data source)
    - BuchungsTyp: Type of attendance/booking
    - Wert: Duration/value in hours
    - CHF: Base rate in CHF
    - CHF + TZ: Rate with cost-of-living adjustment in CHF

    Data is sorted by date then person name.
    """
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)
    if not rate_set:
        return BytesIO()

    # Get all attendences in settlement period
    attendances = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end,
    ).query().all()

    # Get bulk party lookup for buchungen
    buchungen_parliamentarian_ids = {
        str(att.parliamentarian.id) for att in attendances
    }
    buchungen_party_lookup = get_party_lookup(
        session,
        buchungen_parliamentarian_ids,
        settlement_run.start,
        settlement_run.end
    )

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    # Prepare data rows
    data_rows: list[BookingRowData] = []
    for att in attendances:
        parliamentarian = att.parliamentarian

        # Get party from bulk lookup
        party = buchungen_party_lookup[str(parliamentarian.id)]
        party_name = party.name if party else ''

        # Calculate rates
        is_president = any(
            r.role == 'president' for r in parliamentarian.roles
        )
        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=att.type,
            duration_minutes=int(att.duration),
            is_president=is_president,
            commission_type=(
                att.commission.type if att.commission else None
            ),
        )
        rate_with_cola = (Decimal(str(base_rate)) * cola_multiplier).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )

        # Build booking type description
        booking_type = request.translate(TYPES[att.type])
        if (att.type == 'commission' and att.commission
                or att.type == 'study' and att.commission):
            booking_type = f'{booking_type} - {att.commission.name}'

        data_rows.append({
            'date': att.date,
            'person': (f'{parliamentarian.first_name} '
                      f'{parliamentarian.last_name}'),
            'party': party_name,
            'wahlkreis': parliamentarian.district or '',
            'booking_type': booking_type,
            'value': att.calculate_value(),
            'chf': base_rate,
            'chf_with_cola': rate_with_cola
        })

    # Sort by date, then by person name
    data_rows.sort(key=itemgetter('date', 'person'))

    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Buchungen Abrechnungslauf')

    # Define formats
    header_format = workbook.add_format({
        'font_name': 'Times New Roman',
        'font_size': 10
    })
    cell_format = workbook.add_format({
        'font_name': 'Times New Roman',
        'font_size': 10
    })

    # Write headers
    headers = [
        'Datum', 'Person', 'Partei', 'Wahlkreis', 'BuchungsTyp',
        'Wert', 'CHF', 'CHF + TZ'
    ]
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Write data rows
    for row_num, row_data in enumerate(data_rows, 1):
        worksheet.write(
            row_num, 0, row_data['date'].strftime('%d.%m.%Y'), cell_format
        )
        worksheet.write(row_num, 1, row_data['person'], cell_format)
        worksheet.write(row_num, 2, row_data['party'], cell_format)
        worksheet.write(row_num, 3, row_data['wahlkreis'], cell_format)
        worksheet.write(row_num, 4, row_data['booking_type'], cell_format)
        worksheet.write(row_num, 5, float(row_data['value']), cell_format)
        worksheet.write(row_num, 6, float(row_data['chf']), cell_format)
        worksheet.write(
            row_num, 7, float(row_data['chf_with_cola']), cell_format
        )

    # Auto-adjust column widths
    worksheet.set_column('A:A', 12)  # Date
    worksheet.set_column('B:B', 25)  # Person
    worksheet.set_column('C:C', 15)  # Party
    worksheet.set_column('D:D', 15)  # Wahlkreis
    worksheet.set_column('E:E', 30)  # BuchungsTyp
    worksheet.set_column('F:F', 8)   # Wert
    worksheet.set_column('G:G', 10)  # CHF
    worksheet.set_column('H:H', 12)  # CHF + TZ

    workbook.close()
    output.seek(0)
    return output
