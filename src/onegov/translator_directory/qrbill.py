from __future__ import annotations

from io import BytesIO
from onegov.translator_directory import log
from qrbill.bill import QRBill
from stdnum import iban as iban_validator
from weasyprint import HTML  # type: ignore[import-untyped]

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.translator_directory.models.time_report import (
        TranslatorTimeReport,
    )
    from onegov.translator_directory.models.translator import Translator
    from onegov.translator_directory.request import TranslatorAppRequest


def is_valid_iban(value: str | None) -> bool:
    """Check if value is a valid IBAN."""
    if not value:
        return False
    try:
        iban_validator.validate(value)
        return True
    except Exception:
        return False


def generate_translator_qr_bill(
    translator: Translator,
    time_report: TranslatorTimeReport,
    request: TranslatorAppRequest,
) -> bytes | None:
    """
    Generates a QR Bill PDF for a self-employed translator.
    Returns PDF bytes or None if generation fails.
    """

    if not translator.iban or not is_valid_iban(translator.iban):
        request.warning('Invalid or missing IBAN for QR bill generation')
        return None

    if not all(
        [
            translator.first_name,
            translator.last_name,
            translator.address,
            translator.zip_code,
            translator.city,
        ]
    ):
        request.warning('Incomplete address for QR bill generation')
        log.error(f'Incomplete address for translator {translator.id}')
        return None

    # Creditor (translator)
    creditor = {
        'name': f'{translator.first_name} {translator.last_name}',
        'line1': translator.address,
        'line2': f'{translator.zip_code} {translator.city}',
    }

    # Debtor (organization) - hardcoded for now
    # TODO: Move to organization settings
    debtor = {
        'name': 'Zentrale Polizeistation',
        'street': 'Beckstube 1',
        'pcode': '8200',
        'city': 'Schaffhausen',
    }

    # Amount
    amount = '{:.2f}'.format(time_report.total_compensation or 0)

    # Additional information
    additional_information = (
        f'Zeitrapport {time_report.assignment_date.strftime("%d.%m.%Y")}'
    )

    # Language
    language = 'de'  # Default to German
    if hasattr(request, 'locale') and request.locale:
        locale_map = {'de_CH': 'de', 'fr_CH': 'fr', 'it_CH': 'it'}
        language = locale_map.get(request.locale, 'de')

    # Create QR bill
    try:
        bill = QRBill(  # type: ignore[call-overload]
            account=translator.iban,
            creditor=creditor,
            debtor=debtor,
            amount=amount,
            additional_information=additional_information,
            language=language,
        )
    except Exception as e:
        log.exception(e)
        return None

    # Generate SVG
    from io import StringIO

    svg = StringIO()
    bill.as_svg(svg)
    svg_content = svg.getvalue()

    # Convert SVG to PDF using WeasyPrint
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4;
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                }}
                .qr-bill-container {{
                    width: 210mm;
                    height: 297mm;
                    display: flex;
                    align-items: flex-end;
                }}
            </style>
        </head>
        <body>
            <div class="qr-bill-container">
                {svg_content}
            </div>
        </body>
        </html>
        """

        pdf_file = BytesIO()
        HTML(string=html_content).write_pdf(pdf_file)
        return pdf_file.getvalue()

    except Exception as e:
        log.exception(e)
        return None
