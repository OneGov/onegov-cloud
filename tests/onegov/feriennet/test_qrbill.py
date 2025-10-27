from base64 import b64decode
from onegov.activity.models import BookingPeriodInvoice
from onegov.core.utils import Bunch
from onegov.feriennet.qrbill import beneficiary_to_creditor
from onegov.feriennet.qrbill import generate_qr_bill
from onegov.feriennet.qrbill import qr_iban
from onegov.feriennet.qrbill import swiss_iban
from onegov.pay.models import InvoiceReference


SWISS_IBAN = 'CH5604835012345678009'
SWISS_QRIBAN = 'CH4431999123000889012'


def test_beneficiary_to_creditor():
    assert beneficiary_to_creditor(None) is None
    assert beneficiary_to_creditor('') is None
    assert beneficiary_to_creditor('Street') is None
    assert beneficiary_to_creditor('FP Govikon, Rue du Bac, 1234 Govikon') == {
        'name': 'FP Govikon', 'line1': 'Rue du Bac', 'line2': '1234 Govikon'
    }


def test_iban():
    assert swiss_iban(SWISS_IBAN)
    assert swiss_iban('LI21 0881 0000 2324 013A A')
    assert not swiss_iban('DK9520000123456789')

    assert qr_iban(SWISS_QRIBAN)
    assert not qr_iban(SWISS_IBAN)


def test_qrbill():
    def qr_bill(**kwargs):
        enabled = kwargs.pop('enabled', True)
        schema = kwargs.pop('schema', 'feriennet-v1')
        locale = kwargs.pop('locale', 'en_US')
        iban = kwargs.pop('iban', SWISS_IBAN)
        reference = kwargs.pop('reference', 'qebfc27ef12')
        beneficiary = kwargs.pop('beneficiary', 'FerPa, Platz 1, 1234 Govikon')
        amount = kwargs.pop('amount', 10)
        bucket = kwargs.pop('bucket', 'feriennet-v1')
        name = kwargs.pop('name', 'Hans Muster')
        address = kwargs.pop('address', 'Street 123')
        zip_code = kwargs.pop('zip_code', '1234')
        place = kwargs.pop('place', 'Govikon')

        request = Bunch(
            locale=locale,
            app=Bunch(
                org=Bunch(meta={
                    'bank_qr_bill': enabled,
                    'bank_account': iban,
                    'bank_beneficiary': beneficiary
                }),
                invoice_bucket=lambda: bucket
            )
        )
        user = Bunch(
            realname=name,
            data={
                'name': name,
                'address': address,
                'zip_code': zip_code,
                'place': place
            }
        )
        invoice = BookingPeriodInvoice()
        invoice.add('group', 'text', amount, 1, flush=False)
        invoice.references.append(
            InvoiceReference(reference=reference, bucket=bucket, schema=schema)
        )

        result = generate_qr_bill(schema, request, user, invoice)
        if result:
            result = b64decode(result).decode()
        return result

    # feriennet-v1 / en
    result = qr_bill()
    assert 'Receipt' in result
    assert 'CH56 0483 5012 3456 7800 9' in result
    assert 'Additional information' in result
    assert 'Q-EBFC2-7EF12' in result
    assert '10.00' in result
    assert 'FerPa' in result
    assert 'Platz 1' in result
    assert '1234 Govikon' in result
    assert 'Hans Muster' in result
    assert 'Street 123' in result
    assert 'CH-1234 Govikon' in result

    # locales
    assert 'Empfangsschein' in qr_bill(locale='de_CH')
    assert 'Récépissé' in qr_bill(locale='fr_CH')
    assert 'Ricevuta' in qr_bill(locale='it_CH')

    # esr-v1
    result = qr_bill(
        iban=SWISS_QRIBAN,
        schema='esr-v1',
        invoice_bucket='esr-v1',
        reference='277409152814488798004124782'
    )
    assert 'Additional information' not in result
    assert 'Reference' in result
    assert '27 74091 52814 48879 80041 24782' in result

    # silent fixes
    address = ''.join(71 * ['x'])
    assert f'>{address[:70]}<' in qr_bill(address=address)

    # fails
    assert qr_bill(enabled=False) is None
    assert qr_bill(iban=None) is None
    assert qr_bill(iban='') is None
    assert qr_bill(iban='ABCD') is None
    assert qr_bill(beneficiary=None) is None
    assert qr_bill(beneficiary='') is None
    assert qr_bill(beneficiary='Ferienpass') is None
    assert qr_bill(name=None) is None
    assert qr_bill(zip_code=None) is None
    assert qr_bill(place=None) is None
