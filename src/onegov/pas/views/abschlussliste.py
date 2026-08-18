from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from io import BytesIO

import xlsxwriter

from onegov.pas.settlement_data import SettlementData
from onegov.pas.settlement_data import SettlementEntry
from onegov.pas.settlement_data import get_settlement_data


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models.settlement_run import SettlementRun
    from onegov.town6.request import TownRequest


def aggregate_abschlussliste_data(
    settlement_data: SettlementData,
) -> list[dict[str, Any]]:
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
            'presidential_allowance': Decimal('0'),
            'expenses': Decimal('0'),
        }
    )

    parliamentarians = {}
    for entry in settlement_data.attendances:
        parliamentarian = entry.parliamentarian
        parliamentarians[parliamentarian.id] = parliamentarian
        data = parl_data[str(parliamentarian.id)]
        duration_key = f'{entry.attendance_type}_duration'
        compensation_key = f'{entry.attendance_type}_compensation'
        if entry.attendance_type == 'plenary':
            duration_key = 'plenum_duration'
            compensation_key = 'plenum_compensation'
        data[duration_key] += entry.duration_minutes
        data[compensation_key] += entry.compensation.base

    for allowance_entry in settlement_data.allowances:
        parliamentarian = allowance_entry.parliamentarian
        parliamentarians[parliamentarian.id] = parliamentarian
        parl_data[str(parliamentarian.id)][
            'presidential_allowance'
        ] += allowance_entry.compensation.base

    result: list[dict[str, Any]] = []
    for parliamentarian in parliamentarians.values():
        party = settlement_data.party_lookup.get(parliamentarian.id)
        data = parl_data[str(parliamentarian.id)]
        data['parliamentarian'] = parliamentarian
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


def get_abschlussliste_data(
    settlement_run: SettlementRun,
    request: TownRequest,
) -> list[dict[str, Any]]:
    return aggregate_abschlussliste_data(
        get_settlement_data(settlement_run, request)
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
        'Präsidialzulage',
        'Spesen',
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

    settlement_data = get_settlement_data(settlement_run, request)
    data = aggregate_abschlussliste_data(settlement_data)

    for details_row_num, entry in enumerate(
        settlement_data.attendances,
        start=1,
    ):
        parliamentarian = entry.parliamentarian
        party = settlement_data.party_lookup.get(parliamentarian.id)

        details_row = [
            entry.date.strftime('%d.%m.%Y'),
            parliamentarian.last_name,
            parliamentarian.first_name,
            party.name if party else '',
            party.name if party else '',
            entry.type_label,
            entry.commission.name if entry.commission else '',
            entry.value,
            entry.compensation.base,
        ]
        for col, value in enumerate(details_row):
            details_ws.write(details_row_num, col, value, cell_format)

    for row_num, row_data in enumerate(data, 1):
        p = row_data['parliamentarian']

        overview_row = [
            p.last_name, p.first_name, row_data['party'], row_data['faction'],
            row_data['plenum_duration'], row_data['plenum_compensation'],
            row_data['commission_duration']
            + row_data['study_duration']
            + row_data['shortest_duration'],
            row_data['commission_compensation']
            + row_data['study_compensation']
            + row_data['shortest_compensation'],
            row_data['presidential_allowance'],
            row_data['expenses'],
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
    settlement_data = get_settlement_data(settlement_run, request)

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

    attendance_entries = sorted(
        settlement_data.attendances,
        key=lambda entry: (
            entry.date,
            entry.parliamentarian.first_name,
            entry.parliamentarian.last_name,
        ),
    )
    entries: list[SettlementEntry] = [
        *attendance_entries,
        *settlement_data.allowances,
    ]
    for row_num, entry in enumerate(entries, 1):
        parliamentarian = entry.parliamentarian
        party = settlement_data.party_lookup.get(parliamentarian.id)
        worksheet.write(
            row_num,
            0,
            entry.date.strftime('%d.%m.%Y'),
            cell_format,
        )
        worksheet.write(
            row_num,
            1,
            (f'{parliamentarian.first_name} {parliamentarian.last_name}'),
            cell_format,
        )
        worksheet.write(
            row_num,
            2,
            party.name if party else '',
            cell_format,
        )
        worksheet.write(
            row_num,
            3,
            parliamentarian.district or '',
            cell_format,
        )
        worksheet.write(
            row_num,
            4,
            entry.type_description,
            cell_format,
        )
        worksheet.write(
            row_num,
            5,
            float(entry.value),
            cell_format,
        )
        worksheet.write(
            row_num,
            6,
            float(entry.compensation.base),
            cell_format,
        )
        worksheet.write(
            row_num,
            7,
            float(entry.compensation.adjusted),
            cell_format,
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
