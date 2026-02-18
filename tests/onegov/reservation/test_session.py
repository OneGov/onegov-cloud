from __future__ import annotations

import morepath

from datetime import datetime
from libres import new_scheduler
from onegov.core.framework import Framework
from onegov.core.orm import Base as CoreBase
from onegov.core.utils import scan_morepath_modules
from onegov.reservation import LibresIntegration, ResourceCollection
from sqlalchemy import text
from sqlalchemy.orm import mapped_column, registry, DeclarativeBase, Mapped
from uuid import uuid4
from webtest import TestApp as Client


from typing import Any


def test_setup_database(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase):
        registry = registry()

    class App(Framework, LibresIntegration):
        pass

    class Document(Base):
        __tablename__ = 'documents'
        id: Mapped[int] = mapped_column(primary_key=True)

    @App.path(path='/')
    class Root:
        pass

    @App.json(model=Root)
    def get_root(self: Root, request: object) -> object:
        return []

    # this is required for the transactions to actually work, usually this
    # would be onegov.server's job
    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'libres'
    app.configure_application(
        dsn=postgres_dsn,
        base=CoreBase,
        redis_url=redis_url
    )
    app.session_manager.bases.append(Base)
    app.set_application_id('libres/foo')

    c = Client(app)
    c.get('/')

    result = app.session().execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public'"
    ))

    assert not result.all()

    result = app.session().execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'libres-foo'"
    ))

    tables = set(result.scalars())

    assert 'documents' in tables
    assert 'payments_for_reservations_payment' in tables
    assert 'resources' in tables
    assert 'allocations' in tables
    assert 'reserved_slots' in tables
    assert 'reservations' in tables

    app.session_manager.dispose()


def test_libres_context(postgres_dsn: str) -> None:
    class Base(DeclarativeBase):
        registry = registry()

    class App(Framework, LibresIntegration):
        pass

    app = App()
    app.namespace = 'libres'
    app.configure_application(dsn=postgres_dsn, base=CoreBase)
    app.session_manager.bases.append(Base)
    app.set_application_id('libres/foo')
    app.session_manager.set_current_schema('libres-foo')

    result = app.session().execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'libres-foo'"
    ))

    tables = set(result.scalars())

    assert 'payments_for_reservations_payment' in tables
    assert 'resources' in tables
    assert 'allocations' in tables
    assert 'reserved_slots' in tables
    assert 'reservations' in tables

    scheduler = new_scheduler(app.libres_context, uuid4(), 'Europe/Zurich')  # type: ignore[arg-type]
    assert scheduler.managed_allocations().count() == 0

    scheduler.allocate((datetime(2015, 7, 30, 11), datetime(2015, 7, 30, 12)))
    assert scheduler.managed_allocations().count() == 1

    assert app.session_manager is app.libres_context.get_service(
        'session_provider')


def test_transaction_integration(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase):
        registry = registry()

    class App(Framework, LibresIntegration):
        pass

    class Document(Base):
        __tablename__ = 'documents'
        id: Mapped[int] = mapped_column(primary_key=True)

    @App.path(path='/')
    class Root:
        pass

    @App.json(model=Root)
    def handle_root(self: Root, request: Any) -> None:
        collection = ResourceCollection(request.app.libres_context)

        resource = collection.add('Test', 'Europe/Zurich')
        scheduler = resource.get_scheduler(request.app.libres_context)
        scheduler.allocate(
            (datetime(2015, 7, 30, 11), datetime(2015, 7, 30, 12))
        )

        # this will fail and then abort everything
        request.session.add(Document(id=1))
        request.session.add(Document(id=1))

    # this is required for the transactions to actually work, usually this
    # would be onegov.server's job
    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'libres'
    app.configure_application(
        dsn=postgres_dsn,
        base=CoreBase,
        redis_url=redis_url
    )
    app.session_manager.bases.append(Base)
    app.set_application_id('libres/foo')

    c = Client(app)
    try:
        c.get('/', expect_errors=True)
    except Exception:
        pass

    collection = ResourceCollection(app.libres_context)
    assert collection.query().count() == 0
