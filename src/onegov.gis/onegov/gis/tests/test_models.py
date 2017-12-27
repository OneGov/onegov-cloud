from onegov.core.orm import ModelBase
from onegov.core.orm import SessionManager
from onegov.core.orm.mixins import ContentMixin
from onegov.gis.models import Coordinates, CoordinatesMixin
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy.ext.declarative import declarative_base


def test_mutable_coordinates(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Monument(Base, ContentMixin, CoordinatesMixin):
        __tablename__ = 'monument'
        id = Column(Integer, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    session = mgr.session()
    session.add(Monument())
    session.flush()

    washington = session.query(Monument).one()
    assert washington.coordinates.lat is None
    assert washington.coordinates.lon is None
    assert washington.coordinates.zoom is None

    washington = session.query(Monument).one()
    washington.coordinates = Coordinates(38.889484, -77.035278)
    assert washington.coordinates.lat == 38.889484
    assert washington.coordinates.lon == -77.035278
    assert washington.coordinates.zoom is None
    session.flush()

    washington = session.query(Monument).one()
    washington.coordinates.zoom = 10
    session.flush()

    assert session.query(Monument).one().coordinates.zoom == 10

    mgr.dispose()
