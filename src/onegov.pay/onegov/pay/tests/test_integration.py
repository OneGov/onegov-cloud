import logging

from onegov.pay import process_payment, Price
from onegov.pay import CARD_ERRORS


def test_process_manual_payment():
    payment = process_payment('manual', Price(10, 'CHF'))
    assert payment.source == 'manual'
    assert payment.amount == 10
    assert payment.currency == 'CHF'

    payment = process_payment('free', Price(10, 'CHF'))
    assert payment.source == 'manual'
    assert payment.amount == 10
    assert payment.currency == 'CHF'


def test_process_credit_card_payment_successfully():

    class Provider(object):
        def charge(self, amount, currency, token):
            return 'success'

    payment = process_payment('manual', Price(10, 'CHF'), Provider(), 'foobar')
    assert payment.source == 'manual'

    payment = process_payment('free', Price(10, 'CHF'), Provider(), 'foobar')
    assert payment == 'success'

    payment = process_payment('cc', Price(10, 'CHF'), Provider(), 'foobar')
    assert payment == 'success'


def test_process_credit_card_payment_error(capturelog):

    class Provider(object):
        title = 'Foobar'

        def charge(self, amount, currency, token):
            raise CARD_ERRORS[0](None, None, None)

    capturelog.setLevel(logging.ERROR, logger='onegov.pay')

    payment = process_payment('cc', Price(10, 'CHF'), Provider(), 'foobar')
    assert payment is None

    assert capturelog.records()[0].message\
        == 'Processing 10.00 CHF through Foobar with token foobar failed'
