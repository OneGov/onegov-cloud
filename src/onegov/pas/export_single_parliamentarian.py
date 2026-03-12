from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import (
    AttendenceCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.attendence import TYPES
from onegov.pas.utils import is_commission_president
from onegov.pas.utils import format_swiss_number
from onegov.pas.utils import round_to_five_rappen
from onegov.core.utils import module_path
from weasyprint import HTML, CSS  # type: ignore[import-untyped]
from weasyprint.text.fonts import (  # type: ignore[import-untyped]
    FontConfiguration,
)
from datetime import date  # noqa: TC003


from typing import TYPE_CHECKING, Literal, TypedDict
if TYPE_CHECKING:
    from datetime import date
    from onegov.pas.models import PASParliamentarian, RateSet
    from onegov.pas.models.settlement_run import SettlementRun


@dataclass
class ParliamentarianEntry:
    date: date
    type_description: str
    calculated_value: Decimal
    additional_value: Decimal
    base_rate: Decimal
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
    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )
    quarter = settlement_run.get_run_number_for_year(settlement_run.end)
    css_path = module_path(
        'onegov.pas', 'views/templates/parliamentarian_settlement_pdf.css'
    )
    with open(css_path) as f:
        css = CSS(string=f.read())

    data = _get_parliamentarian_settlement_data(
        settlement_run, request, parliamentarian, rate_set
    )
    html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <div class="first-line">
                <p>Staatskanzlei, Seestrasse 2, 6300 Zug</p><br>
            </div>
            <div class="address">
                {parliamentarian.formal_greeting.split()[0]}<br>
                {parliamentarian.first_name} {parliamentarian.last_name}<br>
                {parliamentarian.shipping_address}<br>
                {parliamentarian.shipping_address_zip_code}
                {parliamentarian.shipping_address_city}
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
                    round_to_five_rappen(entry.calculated_value))}</td>
                <td class="numeric">{format_swiss_number(
                    round_to_five_rappen(entry.base_rate))}</td>
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

    # Now, start building the second part of the report document. Notice that
    # this one now is *with* cost of living adjustment.
    total = Decimal('0')
    total = Decimal('0')
    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )
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
        total_value_rounded = round_to_five_rappen(total_value)
        total_value_str = (
            format_swiss_number(total_value_rounded)
            if type_key != 'expenses'
            else '-'
        )
        base_total = type_totals[type_key]['total']
        total_chf = base_total * cola_multiplier
        total_chf_rounded = round_to_five_rappen(total_chf)
        total += total_chf_rounded
        html += f"""
            <tr>
                <td>{type_name}</td>
                <td class="numeric">{total_value_str}</td>
                <td class="numeric">{format_swiss_number(
                    total_chf_rounded)}</td>
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
        stylesheets=[css], font_config=font_config
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
        is_president = is_commission_president(
            parliamentarian, attendence, settlement_run
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
            calculated_value=attendence.calculate_value(),
            additional_value=Decimal('0'),
            base_rate=Decimal(str(base_rate)),
            attendance_type=attendence.type,
        )
        result.append(entry)

    # Sort by date
    result.sort(key=lambda x: x.date)
    return {'entries': result}
