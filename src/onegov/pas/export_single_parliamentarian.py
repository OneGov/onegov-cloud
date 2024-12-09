from onegov.pas.calculate_pay import calculate_rate
from dataclasses import dataclass
from typing import cast
from onegov.pas.collections import (
    AttendenceCollection,
)
from onegov.pas.custom import get_current_rate_set
from decimal import Decimal
from weasyprint import HTML, CSS  # type: ignore[import-untyped]
from weasyprint.text.fonts import (  # type: ignore[import-untyped]
    FontConfiguration,
)
from onegov.pas.models.attendence import TYPES, Attendence
from datetime import date  # noqa: TC003
from typing import Literal, TypedDict


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import Parliamentarian
    from onegov.pas.models.settlement_run import SettlementRun


@dataclass
class ParliamentarianEntry:
    date: date
    type_description: str
    calculated_value: Decimal
    additional_value: Decimal
    base_rate: Decimal
    attendance_type: 'AttendenceType'


AttendenceType = Literal['plenary', 'commission', 'study', 'shortest']


class TypeTotal(TypedDict):
    entries: list[ParliamentarianEntry]
    total: Decimal


TotalType = Literal['plenary', 'commission', 'study', 'shortest', 'expenses']


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.request import TownRequest


def generate_parliamentarian_settlement_pdf(
    settlement_run: 'SettlementRun',
    request: 'TownRequest',
    parliamentarian: 'Parliamentarian',
) -> bytes:
    """Generate PDF for parliamentarian settlement data."""
    font_config = FontConfiguration()
    css = CSS(
        string="""
        @page {
            size: A4;
            margin: 2.5cm 0.75cm 2cm 0.75cm;  /* top right bottom left */
            @top-right {
                content: "Staatskanzlei";
                font-family: Helvetica, Arial, sans-serif;
                font-size: 8pt;
            }
        }

        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 7pt;
            line-height: 1.2;
        }

        .first-line {
            font-size: 7pt;
            text-decoration: underline;
            margin-left: 1.0cm;
            margin-bottom: 0.5cm;
        }
        
        .address {
            margin-left: 1.0cm;
            margin-bottom: 0.5cm;
            font-size: 8pt;
            line-height: 1.4;
        }

        .date {
            margin-left: 1.0cm;
            margin-bottom: 2cm;
            font-size: 8pt;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            table-layout: fixed;
            white-space: nowrap;
        }

        /* Column widths for the first row */
        .header-row td {
            background-color: #707070;
            color: white;
            font-weight: bold;
            text-align: left;
            padding: 2pt;
            border: 1pt solid #000;
        }
        
        /* Remove right border of first column in header row */
        .header-row td:first-child {
            border-right: none;
        }

        .custom-header td:nth-child(1) { width: 100pt; }  /* Parl. Name */
        .custom-header td:nth-child(2) { width: 100pt; }  /* Zug */
        .custom-header td:nth-child(3) { width: 100pt; }  /* Partei */
        .custom-header td:nth-child(4) { width: 135pt; }  /* KR- column */

        th, td {
            padding: 2pt;
            border: 1pt solid #000;
        }

        /* Fixed column widths for main table */
            
        .first-table td:first-child { width: 60pt; }  /* Date column */
        .first-table td:nth-child(2) { width: 300pt; } /* Type - maximum 
        space */
        .first-table td:nth-child(3) { width: 70pt; }  /* Value column */
        .first-table td:last-child { width: 70pt; }    /* CHF column */

        /* Fixed column widths for parliamentarian summary table */
        .parliamentarian-summary-table td:first-child { width: 360pt; }
        .parliamentarian-summary-table td:nth-child(2) { width: 50pt; }
        .parliamentarian-summary-table td:last-child { width: 50pt; }

        .numeric { text-align: right; }

        .first-table tr:nth-child(2) td {
            background-color: #d5d7d9;
        }

        .first-table tr:nth-child(even):not(.total-row) td {
            background-color: #f3f3f3;
        }

        .parliamentarian-summary-table {
            page-break-inside: avoid;
            margin-top: 1cm;
        }

        .parliamentarian-summary-table td {
            font-weight: bold;
            background-color: #d5d7d9;
        }
    """
    )

    data = get_parliamentarian_settlement_data(
        settlement_run, request, parliamentarian
    )

    name = f'{parliamentarian.first_name} {parliamentarian.last_name}'
    html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <div class="first-line">
                <p> Staatskanzlei, Seestrasse 2, 6300 Zug</p><br>
            </div>
            <div class="address">
                {parliamentarian.formal_greeting}<br>
                {parliamentarian.shipping_address}<br>
                {parliamentarian.shipping_address_zip_code}
                {parliamentarian.shipping_address_city}
            </div>

            <div class="date">
                Zug {settlement_run.end.strftime('%d.%m.%Y')}
            </div>

            
            <table class="first-table">
                <thead>
                    <tr class="header-row">
                        <td>{name}</td>
                        <td></td>
                        <td>Zug</td>
                        <td>ALG</td>
                        <td></td>
                        <td>KR-{settlement_run.start.year}-
                        {(settlement_run.start.month-1)//3 + 1:02d}</td>
                    </tr>
                    <tr>
                        <th class="data-column-date">Datum</th>
                        <th class="data-column-type">Typ</th>
                        <th class="data-column-value">Wert</th>
                        <th class="data-column-chf">CHF ohne Tz</th>
                    </tr>
                </thead>
                <tbody>
    """

    type_totals: dict[TotalType, TypeTotal] = {
        cast('TotalType', 'plenary'): {'entries': [], 'total': Decimal('0')},
        cast('TotalType', 'commission'): {'entries': [],
                                          'total': Decimal('0')},
        cast('TotalType', 'study'): {'entries': [], 'total': Decimal('0')},
        cast('TotalType', 'shortest'): {'entries': [], 'total': Decimal('0')},
        cast('TotalType', 'expenses'): {'entries': [], 'total': Decimal('0')},
    }

    for entry in data['entries']:
        html += f"""
            <tr>
                <td>{entry.date.strftime('%d.%m.%Y')}</td>
                <td>{entry.type_description}</td>
                <td class="numeric">{entry.calculated_value}</td>
                <td class="numeric">{entry.base_rate:,.2f}</td>
            </tr>
        """
        if entry.type_description not in ['Total', 'Auszahlung']:
            type_totals[entry.attendance_type]['entries'].append(entry)
            type_totals[entry.attendance_type]['total'] += entry.base_rate

    html += """
        </tbody>
    </table>

    <table class="parliamentarian-summary-table">
        <tbody>
    """

    total = Decimal('0')
    type_mappings = [
        ('Total aller Plenarsitzungen inkl. Teuerungszulage',
         cast('TotalType', 'plenary')),
        ('Total aller Kommissionssitzungen inkl. Teuerungszulage',
         cast('TotalType', 'commission')),
        ('Total aller Aktenstudium inkl. Teuerungszulage',
         cast('TotalType', 'study')),
        ('Total aller Kürzestsitzungen inkl. Teuerungszulage',
         cast('TotalType', 'shortest')),
        ('Total Spesen inkl. Teuerungszulage',
         cast('TotalType', 'expenses')),
    ]
    for type_name, type_key in type_mappings:
        total_value = sum(
            entry.calculated_value
            for entry in type_totals[type_key]['entries']
        )
        total_chf = type_totals[type_key]['total']
        total += total_chf
        html += f"""
            <tr>
                <td>{type_name}</td>
                <td class="numeric">{total_value:,.2f}</td>
                <td class="numeric">{total_chf:,.2f}</td>
            </tr>
        """

    html += f"""
            <tr class="merge-cells">
                <td>Auszahlung</td>
                <td colspan="2" class="numeric">{total:,.2f}</td>
                <td>&nbsp;</td>
            </tr>
        </tbody>
    </table>
    </body>
    </html>
    """

    # Convert numbers to Swiss format
    html = html.replace(',', "'")
    return HTML(string=html).write_pdf(
        stylesheets=[css], font_config=font_config
    )


def get_parliamentarian_settlement_data(
    settlement_run: 'SettlementRun',
    request: 'TownRequest',
    parliamentarian: 'Parliamentarian',
) -> dict[str, list[ParliamentarianEntry]]:
    """Get settlement data for a specific parliamentarian."""
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)

    attendences = (
        AttendenceCollection(
            session,
            date_from=settlement_run.start,
            date_to=settlement_run.end,
        )
        .query()
        .filter(Attendence.parliamentarian_id == parliamentarian.id)
    )

    result = []
    for attendence in attendences:
        is_president = any(
            r.role == 'president' for r in parliamentarian.roles
        )
        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=is_president,
            commission_type=(
                attendence.commission.type
                if attendence.commission
                else None
            ),
        )

        # Build type description
        type_desc = request.translate(TYPES[attendence.type])
        if attendence.commission:
            type_desc = f'{type_desc} - {attendence.commission.name}'

        entry = ParliamentarianEntry(
            date=attendence.date,
            type_description=type_desc,
            calculated_value=Decimal(str(attendence.calculate_value())),
            additional_value=Decimal('0'),
            base_rate=Decimal(str(base_rate)),
            attendance_type=attendence.type,
        )
        result.append(entry)

    # Sort by date
    result.sort(key=lambda x: x.date)
    return {'entries': result}
