from __future__ import annotations

from sedate import utcnow

from onegov.pas.models.presidential_allowance import (
    FIBU_KONTO_ALLOWANCE,
    LOHNART_ALLOWANCE_NR,
)
from onegov.pas.settlement_data import get_settlement_data


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from decimal import Decimal

    from onegov.town6.request import TownRequest
    from onegov.pas.models import (SettlementRun)
    from datetime import date


# Document: 'KR-Entschaedigung - 1.Quartal 2024 (1).csv'


NEW_LOHNART_MAPPING = {
    'plenary': {'nr': '2405', 'text': 'Plenarsitzung KR'},
    'commission': {
        'nr': '2410',
        'text': 'Kommissionssitzung KR'
    },
    'study': {'nr': '2421', 'text': 'Aktenstudium KR'},
    'shortest': {
        'nr': '2415',
        'text': 'Kürzesitzung KR'
    }
}

"""
    FibU-Konten:
    3000.20 für Plenarsitzungen
    3000.30 für Kommissionsitzungen & Aktenstudium
    3000.30 amtlichen Missionen Kantonsratspräsidiums
    3170.1 Fahr- und Verpflegungsspesen
"""

FIBU_KONTEN_MAPPING = {
    'plenary': '3000.20',
    'commission': '3000.30',
    'study': '3000.30',
    'shortest': '3000.30',
    # Note: 3170.1 for Fahr- und Verpflegungsspesen would need to be mapped
    # to a specific attendance type. But Spesen (expenses) not yet implemented
}


def generate_fibu_export_rows(
    settlement_run: SettlementRun,
    request: TownRequest
) -> Iterator[list[str | Decimal | date]]:
    """ Finanzbuchhaltung export. Notice a lot of columns
    are empty, this is by choice. This format is precisely
    required. """

    # Requirement is that this export has no header row, but you
    # can uncommment this block for debugging purposes.
    # yield [
    #     'Personalnummer', 'Vertragsnummer', 'Lohnart / Lohnarten Nr.',
    #     '', '', '', '', '', '', '', '', '',  # D-L empty
    #     'Betrag', '', '', '',  # M-P empty (M is Betrag)
    #     'Bemerkung/Lohnartentext', '',
    #     'Fibu-Konto', 'Kostenstelle / Kostenträger',  # S-T
    #     '', '', '', '', '',  # U-Y empty
    #     'Angabe zum Jahr und zum Quartal', 'Exportdatum'  # Z-AA
    # ]

    settlement_data = get_settlement_data(settlement_run, request)
    quarter = settlement_run.get_run_number_for_year(settlement_run.end)
    year_quarter_str = f'{settlement_run.end.year} Q{quarter}'

    for entry in settlement_data.attendances:
        parliamentarian = entry.parliamentarian
        lohnart_info = NEW_LOHNART_MAPPING.get(entry.attendance_type)

        if not lohnart_info:
            lohnart_nr = ''
            lohnart_text = entry.type_label
        else:
            lohnart_nr = lohnart_info['nr']
            lohnart_text = lohnart_info['text']

        fibu_konto = FIBU_KONTEN_MAPPING.get(entry.attendance_type, '')

        yield [
            parliamentarian.personnel_number or '',
            parliamentarian.contract_number or '',
            lohnart_nr,
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            entry.compensation.adjusted,
            '',
            '',
            '',
            lohnart_text,
            '',
            fibu_konto,
            '1000',
            '',
            '',
            '',
            '',
            '',
            year_quarter_str,
            utcnow().strftime('%d.%m.%Y'),
        ]

    for allowance_entry in settlement_data.allowances:
        parliamentarian = allowance_entry.parliamentarian
        yield [
            parliamentarian.personnel_number or '',
            parliamentarian.contract_number or '',
            LOHNART_ALLOWANCE_NR,
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            allowance_entry.compensation.adjusted,
            '',
            '',
            '',
            allowance_entry.type_description,
            '',
            FIBU_KONTO_ALLOWANCE,
            '1000',
            '',
            '',
            '',
            '',
            '',
            year_quarter_str,
            utcnow().strftime('%d.%m.%Y'),
        ]
