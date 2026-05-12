from __future__ import annotations

from datetime import date
from morepath.authentication import Identity, NO_IDENTITY
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.file.utils import as_fileintent
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import VotumCollection
from onegov.landsgemeinde.models import Assembly, AgendaItem, Votum
from onegov.landsgemeinde.models import LandsgemeindeFile
from onegov.user.models import User
from onegov.user.models import UserGroup


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestApp


def create_user(
    name: str,
    role: str = 'anonymous',
    groups: list[UserGroup] | None = None
) -> User:

    return User(
        realname=name,
        username=f'{name}@example.org',
        password_hash='hash',
        role=role,
        groups=groups or []
    )


def test_security_permissions(landsgemeinde_app: TestApp) -> None:
    session = landsgemeinde_app.session()

    # Remove existing users
    session.query(User).delete()

    # Create test data
    states = ('draft', 'scheduled', 'ongoing', 'completed')
    roles = ('admin', 'editor', 'member')

    # assemblies & attached files
    assemblies: dict[str, Assembly] = {}
    for month, state in enumerate(states, start=1):
        assembly = assemblies.setdefault(
            state,
            Assembly(state=state, date=date(2025, month, 5))
        )
        session.add(assembly)
        assembly.memorial_pdf = (b'', 'test.txt')
        session.flush()

    # agenda items & attached files
    # TODO: Do we want to test all permutations? For now we
    #       just attach it to the last assembly, if we want
    #       the state to propagate to all the children, we
    #       would need to do something more expensive.
    agenda_items: dict[str, AgendaItem] = {}
    for number, state in enumerate(states, start=1):
        agenda_item = agenda_items.setdefault(
            state,
            AgendaItem(
                state=state,
                number=number,
                assembly=assembly
            )
        )
        session.add(agenda_item)
        agenda_item.memorial_pdf = (b'', 'test.txt')
        session.flush()

    # vota & attached files
    # TODO: Do we want to test all permutations? For now we
    #       just attach it to the last agenda item, if we want
    #       the state to propagate to all the children, we
    #       would need to do something more expensive.
    vota: dict[str, Votum] = {}
    for number, state in enumerate(states, start=1):
        votum = vota.setdefault(
            state,
            Votum(
                state=state,
                number=number,
                agenda_item=agenda_item
            )
        )
        session.add(votum)
        file = LandsgemeindeFile()
        file.name = 'test.txt'
        file.reference = as_fileintent(b'', 'test.txt')
        session.add(file)
        votum.files.append(file)
        session.flush()

    # ... users
    users = {}
    for role in roles:
        # global roles, e.g. 'editor'
        user = create_user(role, role)
        users[role] = user
        session.add(user)
    session.flush()

    def permits(user: User | None, model: object, permission: object) -> bool:
        return landsgemeinde_app._permits(
            Identity(
                uid=user.id.hex,
                userid=user.username,
                groupids=frozenset(group.id.hex for group in user.groups),
                role=user.role,
                application_id=landsgemeinde_app.application_id
            ) if user else NO_IDENTITY,
            model,
            permission
        )

    def assert_admin(user: User | None, model: object) -> None:
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert permits(user, model, Secret)

    def assert_editor(user: User | None, model: object) -> None:
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_member(user: User | None, model: object) -> None:
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_anonymous(user: User | None, model: object) -> None:
        assert permits(user, model, Public)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_no_access(user: User | None, model: object) -> None:
        assert not permits(user, model, Public)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    # Assembly & AgendaItemCollection & attached files
    for state, assembly in assemblies.items():
        item_collection = AgendaItemCollection(session, date=assembly.date)
        assert_admin(users['admin'], assembly)
        assert_admin(users['admin'], assembly.memorial_pdf)
        assert_admin(users['admin'], item_collection)
        assert_editor(users['editor'], assembly)
        assert_editor(users['editor'], assembly.memorial_pdf)
        assert_editor(users['editor'], item_collection)
        assert_member(users['member'], assembly)
        assert_member(users['member'], assembly.memorial_pdf)
        assert_member(users['member'], item_collection)
        if state == 'draft':
            # downgrade
            assert_no_access(None, assembly)
            assert_no_access(None, assembly.memorial_pdf)
            assert_no_access(None, item_collection)
        else:
            assert_anonymous(None, assembly)
            assert_anonymous(None, assembly.memorial_pdf)
            assert_anonymous(None, item_collection)

    # AgendaItem & VotumCollection & attached files
    for state, agenda_item in agenda_items.items():
        votum_collection = VotumCollection(
            session,
            date=assembly.date,
            agenda_item_number=agenda_item.number
        )
        assert_admin(users['admin'], agenda_item)
        assert_admin(users['admin'], agenda_item.memorial_pdf)
        assert_admin(users['admin'], votum_collection)
        assert_editor(users['editor'], agenda_item)
        assert_editor(users['editor'], agenda_item.memorial_pdf)
        assert_editor(users['editor'], votum_collection)
        assert_member(users['member'], agenda_item)
        assert_member(users['member'], agenda_item.memorial_pdf)
        assert_member(users['member'], votum_collection)
        if state == 'draft':
            # downgrade
            assert_no_access(None, agenda_item)
            assert_no_access(None, agenda_item.memorial_pdf)
            assert_no_access(None, votum_collection)
        else:
            assert_anonymous(None, agenda_item)
            assert_anonymous(None, agenda_item.memorial_pdf)
            assert_anonymous(None, votum_collection)

    # Votum & attached files
    for state, votum in vota.items():
        assert_admin(users['admin'], votum)
        assert_admin(users['admin'], votum.files[0])
        assert_editor(users['editor'], votum)
        assert_editor(users['editor'], votum.files[0])
        assert_member(users['member'], votum)
        assert_member(users['member'], votum.files[0])
        if state == 'draft':
            # downgrade
            assert_no_access(None, votum)
            assert_no_access(None, votum.files[0])
        else:
            assert_anonymous(None, votum)
            assert_anonymous(None, votum.files[0])
