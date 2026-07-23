from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from onegov.pas.calculate_pay import calculate_attendance_compensation
from onegov.pas.calculate_pay import calculate_compensation
from onegov.pas.collections import (
    AttendenceCollection,
)
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.attendence import TYPES
from onegov.pas.models.presidential_allowance import (
    LOHNART_ALLOWANCE_TEXT,
    PresidentialAllowance,
)
from onegov.pas.utils import is_president_for_attendance
from onegov.pas.utils import format_swiss_number
from onegov.core.utils import module_path
from weasyprint import HTML, CSS  # type: ignore[import-untyped]
from weasyprint.text.fonts import (  # type: ignore[import-untyped]
    FontConfiguration,
)

from typing import TYPE_CHECKING, Literal, TypedDict
if TYPE_CHECKING:
    from datetime import date  # noqa: TC003
    from onegov.pas.models import PASParliamentarian, RateSet
    from onegov.pas.models.settlement_run import SettlementRun


@dataclass
class ParliamentarianEntry:
    date: date
    type_description: str
    calculated_value: Decimal
    base_rate: Decimal
    adjusted_rate: Decimal
    attendance_type: AttendenceType


AttendenceType = Literal['plenary', 'commission', 'study', 'shortest']


class TypeTotal(TypedDict):
    entries: list[ParliamentarianEntry]
    total: Decimal


TotalType = Literal['plenary', 'commission', 'study', 'shortest', 'expenses']


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.request import TownRequest


def generate_parliamentarian_settlement_pdf(
    settlement_run: SettlementRun,
    request: TownRequest,
    parliamentarian: PASParliamentarian,
) -> bytes:
    """Generate PDF for parliamentarian settlement data."""
    font_config = FontConfiguration()
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)
    quarter = settlement_run.get_run_number_for_year(settlement_run.end)
    css_path = module_path(
        'onegov.pas', 'views/templates/parliamentarian_settlement_pdf.css'
    )
    with open(css_path) as f:
        css = CSS(string=f.read())
    logo_path = module_path('onegov.agency', 'static/logos/canton-zg-bw.svg')
    logo_css = CSS(
        string=f"""
        @page {{
            @top-left {{
                content: url('file://{logo_path}');
                width: 3cm;
            }}
        }}
    """
    )

    data = _get_parliamentarian_settlement_data(
        settlement_run, request, parliamentarian, rate_set
    )
    allowances = (
        PresidentialAllowanceCollection(
            session,
            settlement_run_id=settlement_run.id,
        )
        .query()
        .filter(PresidentialAllowance.parliamentarian_id == parliamentarian.id)
        .all()
    )
    full_name = (
        f'{parliamentarian.first_name} '
        f'{parliamentarian.last_name}'
    )
    html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <div class="address-block">
                <div class="first-line">
                    Staatskanzlei, Seestrasse 2, 6300 Zug
                </div>
                <div class="address">
                    {parliamentarian.formal_greeting.split()[0]}<br>
                    {full_name}<br>
                    {parliamentarian.shipping_address}<br>
                    {parliamentarian.shipping_address_zip_code}
                    {parliamentarian.shipping_address_city}
                </div>
            </div>

            <div class="date">
                Zug, {settlement_run.end.strftime('%d.%m.%Y')}
            </div>

            <h2 class="title">
                Abrechnung {quarter}. Quartal {settlement_run.end.year}
            </h2>
            <table class="first-table">
                <thead>

                    <tr class="col-types">
                        <th class="data-column-date">Datum</th>
                        <th class="data-column-type">Typ</th>
                        <th class="data-column-value">Wert</th>
                        <th class="data-column-chf">CHF ohne Tz</th>
                    </tr>
                </thead>
                <tbody>
    """

    type_totals: dict[TotalType, TypeTotal] = {
        'plenary': {'entries': [], 'total': Decimal('0')},
        'commission': {'entries': [], 'total': Decimal('0')},
        'study': {'entries': [], 'total': Decimal('0')},
        'shortest': {'entries': [], 'total': Decimal('0')},
        'expenses': {'entries': [], 'total': Decimal('0')},
    }

    for entry in data['entries']:
        html += f"""
            <tr>
                <td>{entry.date.strftime('%d.%m.%Y')}</td>
                <td>{entry.type_description}</td>
                <td class="numeric">{format_swiss_number(
                    entry.calculated_value)}</td>
                <td class="numeric">{format_swiss_number(
                    entry.base_rate)}</td>
            </tr>
        """
        if entry.type_description not in ['Total', 'Auszahlung']:
            type_totals[entry.attendance_type]['entries'].append(entry)
            type_totals[entry.attendance_type]['total'] += entry.adjusted_rate

    allowance_total = Decimal('0')
    for allowance in allowances:
        compensation = calculate_compensation(
            allowance.amount,
            rate_set.cost_of_living_adjustment,
        )
        allowance_total += compensation.adjusted
        html += f"""
            <tr>
                <td>{settlement_run.end.strftime('%d.%m.%Y')}</td>
                <td>{LOHNART_ALLOWANCE_TEXT}</td>
                <td class="numeric">{format_swiss_number(
                    compensation.base)}</td>
                <td class="numeric">{format_swiss_number(
                    compensation.base)}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>

    <table class="parliamentarian-summary-table">
        <tbody>
    """

    # Now, start building the second part of the report document. Notice that
    # this one now is *with* cost of living adjustment.
    total = Decimal('0')
    type_mappings: list[tuple[str, TotalType]] = [
        ('Total aller Plenarsitzungen inkl. Teuerungszulage',
         'plenary'),
        ('Total aller Kommissionssitzungen inkl. Teuerungszulage',
         'commission'),
        ('Total aller Aktenstudium inkl. Teuerungszulage',
         'study'),
        ('Total aller Kürzestsitzungen inkl. Teuerungszulage',
         'shortest'),
        ('Total Spesen inkl. Teuerungszulage',
         'expenses'),
    ]
    for type_name, type_key in type_mappings:
        total_value = sum(
            entry.calculated_value
            for entry in type_totals[type_key]['entries']
        )
        total_value_str = (
            format_swiss_number(total_value) if type_key != 'expenses' else '-'
        )
        adjusted_total = type_totals[type_key]['total']
        total += adjusted_total
        html += f"""
            <tr>
                <td>{type_name}</td>
                <td class="numeric">{total_value_str}</td>
                <td class="numeric">{format_swiss_number(
                    adjusted_total)}</td>
            </tr>
        """
    if allowance_total:
        total += allowance_total
        html += f"""
            <tr>
                <td>Total {LOHNART_ALLOWANCE_TEXT}</td>
                <td class="numeric">-</td>
                <td class="numeric">{format_swiss_number(
                    allowance_total)}</td>
            </tr>
        """

    html += f"""
            <tr class="merge-cells">
                <td>Auszahlung</td>
                <td colspan="2" class="numeric">{format_swiss_number(
                    total)}</td>
            </tr>
        </tbody>
    </table>
    </body>
    </html>
    """
    return HTML(string=html).write_pdf(
        stylesheets=[css, logo_css], font_config=font_config
    )


def _get_parliamentarian_settlement_data(
    settlement_run: SettlementRun,
    request: TownRequest,
    parliamentarian: PASParliamentarian,
    rate_set: RateSet,
) -> dict[str, list[ParliamentarianEntry]]:
    """Get settlement data for a specific parliamentarian."""
    session = request.session

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
        is_president = is_president_for_attendance(
            parliamentarian,
            attendence,
        )
        compensation = calculate_attendance_compensation(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=attendence.duration,
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
            calculated_value=attendence.calculate_value(),
            base_rate=compensation.base,
            adjusted_rate=compensation.adjusted,
            attendance_type=attendence.type,
        )
        result.append(entry)

    # Sort by date
    result.sort(key=lambda x: x.date)
    return {'entries': result}
