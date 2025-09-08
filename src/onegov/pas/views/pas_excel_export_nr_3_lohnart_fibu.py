from __future__ import annotations
from decimal import Decimal
from sedate import utcnow
from collections.abc import Iterator

from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import (
    AttendenceCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.models import (
    SettlementRun,
)
from onegov.pas.models.attendence import TYPES

from onegov.town6.request import TownRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from collections.abc import Iterator


NEW_LOHNART_MAPPING = {
    'plenary': {'nr': '2405', 'text': 'Sitzungsentschädigung KR'},
    'commission': {
        'nr': '2410',
        'text': 'Kommissionsentschädigung KR inkl. Kürzestsitzungen'
    },
    'study': {'nr': '2421', 'text': 'Aktenstudium Kantonsrat'},
    'shortest': {
        'nr': '2410',
        'text': 'Kommissionsentschädigung KR inkl. Kürzestsitzungen'
    }
}


def generate_xlsx_export_rows(
    settlement_run: SettlementRun,
    request: TownRequest
) -> Iterator[list[str | Decimal | date]]:

    yield [
        'Personalnummer', 'Vertragsnummer', 'Lohnart / Lohnarten Nr.',
        '', '', '', '', '', '', '', '', '',  # D-L empty
        'Betrag', '', '', '',  # M-P empty (M is Betrag)
        'Bemerkung/Lohnartentext, welche auf der Lohnabrechnung erscheint', '',
        'Fibu-Konto', 'Kostenstelle / Kostenträger',  # S-T
        '', '', '', '', '',  # U-Y empty
        'Angabe zum Jahr und zum Quartal', 'Exportdatum'  # Z-AA
    ]

    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)
    if not rate_set:
        return

    # Get all attendences in period
    attendences = AttendenceCollection(
        session,
        date_from=settlement_run.start,
        date_to=settlement_run.end
    ).query()

    cola_multiplier = Decimal(
        str(1 + (rate_set.cost_of_living_adjustment / 100))
    )
    quarter = settlement_run.get_run_number_for_year(settlement_run.end)
    year_quarter_str = f'{settlement_run.end.year} Q{quarter}'

    for attendance in attendences:
        parliamentarian = attendance.parliamentarian
        lohnart_info = NEW_LOHNART_MAPPING.get(attendance.type)

        if not lohnart_info:
            lohnart_nr = ''
            lohnart_text = request.translate(TYPES.get(
                attendance.type, ''))
        else:
            lohnart_nr = lohnart_info['nr']
            lohnart_text = lohnart_info['text']

        is_president = any(r.role == 'president'
                           for r in parliamentarian.roles)
        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendance.type,
            duration_minutes=int(attendance.duration),
            is_president=is_president,
            commission_type=(
                attendance.commission.type if attendance.commission else None
            )
        )
        rate_with_cola = Decimal(base_rate * cola_multiplier)

        # Some columns are left empty on purpose (this is what is asked)
        yield [
            parliamentarian.personnel_number or '', '', lohnart_nr,
            '', '', '', '', '', '', '', '', '', rate_with_cola,
            '', '', '', lohnart_text, '', '', '',
            '', '', '', '', '', year_quarter_str, utcnow().strftime('%d.%m.%Y')
        ]
