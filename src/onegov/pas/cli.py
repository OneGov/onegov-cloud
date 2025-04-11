from __future__ import annotations

import click
from onegov.core.cli import command_group
from onegov.pas.excel_header_constants import (
    commission_expected_headers_variant_1,
    commission_expected_headers_variant_2,
)
from onegov.pas.data_import import import_commissions


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.pas.app import PasApp
    from onegov.pas.app import TownRequest
    from typing import TypeAlias

    Processor: TypeAlias = Callable[[TownRequest, PasApp], None]


cli = command_group()


@cli.command('import-commission-data')
@click.argument('excel_file', type=click.Path(exists=True))
def import_commission_data(
    excel_file: str,
) -> Processor:
    """Import commission data from an Excel or csv file.

    Assumes that the name of the commission is the filename.

    Each row of this import contains a single line, which is a single
    parliamentarian and all the information about them.

    Example:
        onegov-pas --select '/onegov_pas/zug' import-commission-data \
            "Kommission_Gesundheit_und_Soziales.xlsx"
    """

    def import_data(request: TownRequest, app: PasApp) -> None:

        try:
            import_commissions(
                excel_file,
                request.session,
                excel_file,
                expected_headers=commission_expected_headers_variant_1,
            )
            click.echo('Ok.')
        except Exception:
            click.echo('Trying the other variant of headers...')
            import_commissions(
                excel_file,
                request.session,
                excel_file,
                expected_headers=commission_expected_headers_variant_2,
            )
            click.echo('Ok.')

    return import_data
