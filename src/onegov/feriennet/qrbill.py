from base64 import b64encode
from io import StringIO
from qrbill.bill import QRBill, IBAN_ALLOWED_COUNTRIES, QR_IID
from stdnum import iban


def beneficiary_to_creditor(value):
    value = value or ''
    lines = [line.strip() for line in value.split(',') if line.strip()]
    if len(lines) == 3:
        return {
            'name': lines[0],
            'line1': lines[1],
            'line2': lines[2],
        }
    return None


def swiss_iban(value):
    value = iban.validate(value)
    if value[:2] in IBAN_ALLOWED_COUNTRIES:
        return True
    return False


def qr_iban(value):
    value = iban.validate(value)
    if QR_IID['start'] <= int(value[4:9]) <= QR_IID['end']:
        return True
    return False


def generate_qr_bill(schema, request, user, invoice):
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
    ref_number = None
    extra_infos = None
    if schema == 'feriennet-v1':
        extra_infos = invoice.readable_by_bucket(invoice_bucket)
    else:
        if not qr_iban(account):
            return None
        ref_number = invoice.readable_by_bucket(invoice_bucket)

    # Creditor (mandatory)
    beneficiary = request.app.org.meta.get('bank_beneficiary', None)
    if not beneficiary:
        return None
    creditor = beneficiary_to_creditor(beneficiary)
    if not creditor:
        return None

    # Debtor
    debtor = {
        'name': user.data.get('organisation') or user.realname,
        'street': user.data.get('address', None),
        'pcode': user.data.get('zip_code', None),
        'city': user.data.get('place', None),
    }
    if not debtor['name'] or not debtor['pcode'] or not debtor['city']:
        return None

    # Language
    language = {'de_CH': 'de', 'fr_CH': 'fr', 'it_CH': 'it'}.get(
        request.locale, 'en'
    )

    # Create bill
    bill = QRBill(
        account=account,
        creditor=creditor,
        debtor=debtor,
        amount='{:.2f}'.format(invoice.outstanding_amount),
        ref_number=ref_number,
        extra_infos=extra_infos,
        language=language,
    )

    # Save as SVG
    svg = StringIO()
    bill.as_svg(svg)
    svg.seek(0)
    svg = svg.read()

    # Encode
    return b64encode(svg.encode('utf-8'))
