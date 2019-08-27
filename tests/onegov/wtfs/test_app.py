from onegov.wtfs.models import PaymentType
from transaction import commit


def test_app_principal(wtfs_app):
    assert wtfs_app.principal


def test_app_initial_content(wtfs_app):
    session = wtfs_app.session()
    session.query(PaymentType).delete()

    wtfs_app.add_initial_content()
    commit()

    payment_types = dict(
        session.query(PaymentType.name, PaymentType._price_per_quantity)
    )
    assert payment_types == {'normal': 700, 'spezial': 850}
