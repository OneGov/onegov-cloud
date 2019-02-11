from onegov.wtfs.models import Municipality
from transaction import commit


def test_app_principal(wtfs_app):
    assert wtfs_app.principal


def test_app_initial_content(wtfs_app):
    wtfs_app.add_initial_content()
    commit()

    session = wtfs_app.session()
    item = session.query(Municipality).filter_by(name="Andelfingen").first()
    assert item
    assert item.group.name == "Andelfingen"
