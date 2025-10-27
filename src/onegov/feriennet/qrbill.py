from __future__ import annotations

from base64 import b64encode
from io import StringIO
from onegov.feriennet import log
from onegov.feriennet.utils import NAME_SEPARATOR
from qrbill.bill import QRBill, IBAN_ALLOWED_COUNTRIES, QR_IID
from stdnum import iban


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models import BookingPeriodInvoice
    from onegov.feriennet.request import FeriennetRequest
    from onegov.user import User


def beneficiary_to_creditor(value: str | None) -> dict[str, str] | None:
    value = value or ''
    lines = [line.strip() for line in value.split(',') if line.strip()]
    if len(lines) == 3:
        return {
            'name': lines[0],
            'line1': lines[1],
            'line2': lines[2],
        }
    return None


def swiss_iban(value: str) -> bool:
    value = iban.validate(value)
    if value[:2] in IBAN_ALLOWED_COUNTRIES:
        return True
    return False


def qr_iban(value: str) -> bool:
    value = iban.validate(value)
    if QR_IID['start'] <= int(value[4:9]) <= QR_IID['end']:
        return True
    return False


SUPPORTED_LANGUAGES: dict[str | None, Literal['en', 'de', 'fr', 'it']] = {
    'de_CH': 'de', 'fr_CH': 'fr', 'it_CH': 'it'
}


def generate_qr_bill(
    schema: str,
    request: FeriennetRequest,
    user: User,
    invoice: BookingPeriodInvoice
) -> bytes | None:
    """ Generates a QR Bill and returns it as base64 encoded SVG. """

    # Check if enabled
    if not request.app.org.meta.get('bank_qr_bill', None):
        return None

    # IBAN (mandatory)
    account = request.app.org.meta.get('bank_account', None)
    if not account or not iban.is_valid(account):
        return None
    if not swiss_iban(account):
        return None

    # Reference number
    invoice_bucket = request.app.invoice_bucket()
    reference_number = None
    additional_information = ''
    if schema == 'feriennet-v1':
        additional_information = (
            invoice.readable_by_bucket(invoice_bucket) or '')
    else:
        if not qr_iban(account):
            return None
        reference_number = invoice.readable_by_bucket(invoice_bucket)

    # Creditor (mandatory)
    beneficiary = request.app.org.meta.get('bank_beneficiary', None)
    if not beneficiary:
        return None
    creditor = beneficiary_to_creditor(beneficiary)
    if not creditor:
        return None

    # Debtor
    realname = (user.realname or '').replace(NAME_SEPARATOR, ' ')
    debtor: dict[str, str | None] = {
        'name': user.data.get('organisation') or realname,
        'street': user.data.get('address', None),
        'pcode': user.data.get('zip_code', None),
        'city': user.data.get('place', None),
    }
    if not debtor['name'] or not debtor['pcode'] or not debtor['city']:
        log.error('Not enough debtor information for qr bill: {user.realname}')
        return None
    if debtor['street'] and len(debtor['street']) > 70:
        debtor['street'] = debtor['street'][:70]
    if debtor['pcode'] and len(debtor['pcode']) > 16:
        debtor['pcode'] = debtor['pcode'][:16]

    # Language
    language = SUPPORTED_LANGUAGES.get(request.locale, 'en')

    # Create bill
    try:
        bill = QRBill(
            account=account,
            creditor=creditor,
            debtor=debtor,
            amount='{:.2f}'.format(invoice.outstanding_amount),
            reference_number=reference_number,
            additional_information=additional_information,
            language=language,
        )
    except Exception as e:
        log.exception(e)
        return None

    # Save as SVG
    svg = StringIO()
    bill.as_svg(svg)

    # Encode
    return b64encode(svg.getvalue().encode('utf-8'))
