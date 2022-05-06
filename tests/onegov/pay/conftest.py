import pytest
import transaction

from onegov.pay.models import Payment


@pytest.fixture(scope='function', autouse=True)
def reset_payment():
    yield

    # during testing we need to reset the links created on the payment
    # model - in reality this is not an issue as we don't define the same
    # models over and over
    classes = [Payment]

    while classes:
        cls = classes.pop()

        # todo: it seems that we have a problem that depending on the test/
        # selection of tests and/or used fixtures different models/table
        # are created
        for key in getattr(Payment, 'registered_links', []) or []:
            if key in cls.__mapper__._props:
                del cls.__mapper__._props[key]

        classes.extend(cls.__subclasses__())

    if Payment.registered_links:
        Payment.registered_links.clear()

    transaction.abort()
