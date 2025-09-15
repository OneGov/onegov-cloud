from __future__ import annotations
from collections import defaultdict
from io import BytesIO
from decimal import Decimal
from operator import itemgetter
import xlsxwriter   # type: ignore[import-untyped]

from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import (
    AttendenceCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.utils import (
    get_parliamentarians_with_settlements,
)

from onegov.pas.models.attendence import TYPES


from typing import Any, TypedDict, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.town6.request import TownRequest
    from onegov.pas.models.settlement_run import SettlementRun


class BookingRowData(TypedDict):
    date: date
    person: str
    party: str
    wahlkreis: str
    booking_type: str
    value: Decimal
    chf: Decimal
    chf_with_cola: Decimal

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

    # Details tab
    details_ws = workbook.add_worksheet('Details')
    details_headers = [
        'Name', 'Vorname', 'Partei', 'Fraktion',
        'Plenum / Kommission Zeit', 'Entschädigung',
        'Aktenstudium Zeit', 'Aktenstudium Entschädigung',
        'Kürzestsitzungen Zeit', 'Kürzestsitzungen Entschädigung'
    ]
    for col, header in enumerate(details_headers):
        details_ws.write(0, col, header, header_format)

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
        for col, value in enumerate(details_row):
            details_ws.write(row_num, col, value, cell_format)

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

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )

    # Prepare data rows
    data_rows: list[BookingRowData] = []
    for att in attendances:
        parliamentarian = att.parliamentarian

        # Get party for this parliamentarian during the settlement period
        party = parliamentarian.get_party_during_period(
            settlement_run.start,
            settlement_run.end,
            session
        )
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
        rate_with_cola = Decimal(str(base_rate)) * cola_multiplier

        # Build booking type description
        booking_type = request.translate(TYPES[att.type])
        if (att.type == 'commission' and att.commission
                or att.type == 'study' and att.commission):
            booking_type = f'{booking_type} - {att.commission.name}'

        # TODO: Determine source for Wahlkreis/electoral district
        # This appears to be the municipality/constituency the
        # parliamentarian represents
        wahlkreis = ''  # Leave blank until data source is determined

        data_rows.append({
            'date': att.date,
            'person': (f'{parliamentarian.first_name} '
                      f'{parliamentarian.last_name}'),
            'party': party_name,
            'wahlkreis': wahlkreis,
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

    # Write headers
    headers = [
        'Datum', 'Person', 'Partei', 'Wahlkreis', 'BuchungsTyp',
        'Wert', 'CHF', 'CHF + TZ'
    ]
    worksheet.write_row(0, 0, headers)

    # Format headers
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#D7E4BC',
        'border': 1
    })
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # Write data rows
    for row_num, row_data in enumerate(data_rows, 1):
        worksheet.write(row_num, 0, row_data['date'].strftime('%d.%m.%Y'))
        worksheet.write(row_num, 1, row_data['person'])
        worksheet.write(row_num, 2, row_data['party'])
        worksheet.write(row_num, 3, row_data['wahlkreis'])
        worksheet.write(row_num, 4, row_data['booking_type'])
        worksheet.write(row_num, 5, float(row_data['value']))
        worksheet.write(row_num, 6, float(row_data['chf']))
        worksheet.write(row_num, 7, float(row_data['chf_with_cola']))

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
