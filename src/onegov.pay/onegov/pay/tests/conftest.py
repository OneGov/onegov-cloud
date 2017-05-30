import pytest

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

        for key in Payment.registered_links:
            delattr(cls, key)
            del cls.__mapper__._props[key]

        classes.extend(cls.__subclasses__())

    Payment.registered_links.clear()
