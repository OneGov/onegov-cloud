from __future__ import annotations

import transaction

from morepath import Identity
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.ticket import Ticket
from onegov.ticket import TicketPermission
from onegov.user.models import User
from onegov.user.models import UserGroup
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from .conftest import Client, TestOrgApp


def test_security_ticket_permissions(
    client: Client[TestOrgApp],
    test_password: str
) -> None:

    session = client.app.session()

    # Remove existing users
    session.query(User).delete()

    # Create test data
    # ... user groups
    def create_group(name: str) -> UserGroup:
        result = UserGroup(name=name)
        session.add(result)
        return result

    groups = {
        'HR': [create_group('HR')],
        'Steueramt': [create_group('Steueramt')],
        'Sekretariat': [create_group('Sekretariat')],
    }
    groups['HR+Steueramt'] = groups['HR'] + groups['Steueramt']

    # ... users
    def create_user(
        name: str,
        role: str,
        groups: list[UserGroup] | None = None
    ) -> User:
        result = User(
            realname=name,
            username=f'{name}@example.org',
            password_hash=test_password,
            role=role,
            groups=groups or []
        )
        session.add(result)
        return result

    roles = ('admin', 'editor', 'supporter', 'member', 'anonymous')
    users = {}
    for role in roles:
        users[role] = create_user(role, role)
        for prefix, group in groups.items():
            name = f'{prefix}-{role}'
            users[name] = create_user(name, role, group)

    # ... permissions
    def create_permission(
        handler_code: str,
        group: str | None,
        user_group: UserGroup,
        exclusive: bool = True
    ) -> TicketPermission:
        result = TicketPermission(
            handler_code=handler_code,
            group=group,
            user_group=user_group,
            exclusive=exclusive,
            immediate_notification=True,
        )
        session.add(result)
        return result

    create_permission('PER', None, groups['HR'][0])
    create_permission('FRM', 'Steuererklärung', groups['Steueramt'][0])
    create_permission('FRM', None, groups['Sekretariat'][0])
    # shared non-exclusive permission should mean both groups have access
    create_permission(
        'FRM',
        'Steuererklärung',
        groups['Sekretariat'][0],
        exclusive=False
    )
    # a sole non-exclusive permission should mean all groups have access
    create_permission('EVN', None, groups['Sekretariat'][0], exclusive=False)
    create_permission('RSV', 'A', groups['Sekretariat'][0])

    # ... tickets
    def create_ticket(
        handler_code: str,
        group: str = ''
    ) -> Ticket:
        result = Ticket(
            number=f'{handler_code}-{group}-1',
            title=f'{handler_code}-{group}',
            group=group,
            handler_code=handler_code,
            handler_id=uuid4().hex,
            state='open'
        )
        session.add(result)
        return result

    tickets = {
        'EVN': create_ticket('EVN'),
        'PER': create_ticket('PER'),
        'FRM-S': create_ticket('FRM', 'Steuererklärung'),
        'FRM-W': create_ticket('FRM', 'Wohnsitzbestätigung'),
        'RSV': create_ticket('RSV'),
        'RSV-A': create_ticket('RSV', 'A'),
    }
    ticket_nrs = {
        group: ticket.number
        for group, ticket in tickets.items()
    }

    session.flush()

    # Test permissions

    def permits(user: User, model: object, permission: object) -> bool:
        return client.app._permits(
            Identity(
                uid=user.id.hex,
                userid=user.username,
                groupids=frozenset(group.id.hex for group in user.groups),
                role=user.role,
                application_id=client.app.application_id
            ),
            model,
            permission
        )

    def assert_admin(user: User, model: object) -> None:
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert permits(user, model, Secret)

    def assert_editor(user: User, model: object) -> None:
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_member(user: User, model: object) -> None:
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_anonymous(user: User, model: object) -> None:
        assert permits(user, model, Public)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    # no permission defined
    ticket = tickets['EVN']
    assert_admin(users['admin'], ticket)
    assert_editor(users['editor'], ticket)
    assert_editor(users['supporter'], ticket)
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group_name in groups:
        assert_admin(users[f'{group_name}-admin'], ticket)
        assert_editor(users[f'{group_name}-editor'], ticket)
        assert_editor(users[f'{group_name}-supporter'], ticket)
        assert_member(users[f'{group_name}-member'], ticket)
        assert_anonymous(users[f'{group_name}-anonymous'], ticket)

    ticket = tickets['RSV']
    assert_admin(users['admin'], ticket)
    assert_editor(users['editor'], ticket)
    assert_editor(users['supporter'], ticket)
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group_name in groups:
        assert_admin(users[f'{group_name}-admin'], ticket)
        assert_editor(users[f'{group_name}-editor'], ticket)
        assert_editor(users[f'{group_name}-supporter'], ticket)
        assert_member(users[f'{group_name}-member'], ticket)
        assert_anonymous(users[f'{group_name}-anonymous'], ticket)

    # globally exclude
    ticket = tickets['PER']
    assert_admin(users['admin'], ticket)
    assert_member(users['editor'], ticket)  # downgraded
    assert_member(users['supporter'], ticket)  # downgraded
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group_name in ('Sekretariat', 'Steueramt'):
        assert_admin(users[f'{group_name}-admin'], ticket)
        assert_member(users[f'{group_name}-editor'], ticket)  # downgraded
        assert_member(users[f'{group_name}-supporter'], ticket)  # downgraded
        assert_member(users[f'{group_name}-member'], ticket)
        assert_anonymous(users[f'{group_name}-anonymous'], ticket)
    assert_admin(users['HR-admin'], ticket)
    assert_editor(users['HR-editor'], ticket)
    assert_editor(users['HR-supporter'], ticket)
    assert_member(users['HR-member'], ticket)
    assert_anonymous(users['HR-anonymous'], ticket)
    assert_admin(users['HR+Steueramt-admin'], ticket)
    assert_editor(users['HR+Steueramt-editor'], ticket)
    assert_editor(users['HR+Steueramt-supporter'], ticket)
    assert_member(users['HR+Steueramt-member'], ticket)
    assert_anonymous(users['HR+Steueramt-anonymous'], ticket)

    # specifically exclude (except from shared non-exclusive permissions)
    ticket = tickets['FRM-S']
    assert_admin(users['admin'], ticket)
    assert_member(users['editor'], ticket)  # downgraded
    assert_member(users['supporter'], ticket)  # downgraded
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    assert_admin(users['HR-admin'], ticket)
    assert_member(users['HR-editor'], ticket)  # downgraded
    assert_member(users['HR-supporter'], ticket)  # downgraded
    assert_member(users['HR-member'], ticket)
    assert_anonymous(users['HR-anonymous'], ticket)
    for group_name in ('Steueramt', 'HR+Steueramt', 'Sekretariat'):
        assert_admin(users[f'{group_name}-admin'], ticket)
        assert_editor(users[f'{group_name}-editor'], ticket)
        assert_editor(users[f'{group_name}-supporter'], ticket)
        assert_member(users[f'{group_name}-member'], ticket)
        assert_anonymous(users[f'{group_name}-anonymous'], ticket)

    ticket = tickets['FRM-W']
    assert_admin(users['admin'], ticket)
    assert_member(users['editor'], ticket)  # downgraded
    assert_member(users['supporter'], ticket)  # downgraded
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group_name in ('Steueramt', 'HR', 'HR+Steueramt'):
        assert_admin(users[f'{group_name}-admin'], ticket)
        assert_member(users[f'{group_name}-editor'], ticket)  # downgraded
        assert_member(users[f'{group_name}-supporter'], ticket)  # downgraded
        assert_member(users[f'{group_name}-member'], ticket)
        assert_anonymous(users[f'{group_name}-anonymous'], ticket)
    assert_admin(users['Sekretariat-admin'], ticket)
    assert_editor(users['Sekretariat-editor'], ticket)
    assert_editor(users['Sekretariat-supporter'], ticket)
    assert_member(users['Sekretariat-member'], ticket)
    assert_anonymous(users['Sekretariat-anonymous'], ticket)

    ticket = tickets['RSV-A']
    assert_admin(users['admin'], ticket)
    assert_member(users['editor'], ticket)  # downgraded
    assert_member(users['supporter'], ticket)  # downgraded
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group_name in ('Steueramt', 'HR', 'HR+Steueramt'):
        assert_admin(users[f'{group_name}-admin'], ticket)
        assert_member(users[f'{group_name}-editor'], ticket)  # downgraded
        assert_member(users[f'{group_name}-supporter'], ticket)  # downgraded
        assert_member(users[f'{group_name}-member'], ticket)
        assert_anonymous(users[f'{group_name}-anonymous'], ticket)
    assert_admin(users['Sekretariat-admin'], ticket)
    assert_editor(users['Sekretariat-editor'], ticket)
    assert_editor(users['Sekretariat-supporter'], ticket)
    assert_member(users['Sekretariat-member'], ticket)
    assert_anonymous(users['Sekretariat-anonymous'], ticket)


    # check what's visible in the tickets list
    transaction.commit()

    def assert_visible_tickets(
        username: str,
        visible: Collection[str],
        code: str = 'ALL',
        status: int | None = None
    ) -> None:
        instance = client.spawn()
        instance.login(f'{username}@example.org', 'hunter2')
        tickets = instance.get(
            f'/tickets/{code}/all',
            expect_errors=status is not None
        )
        if status is not None:
            assert status == tickets.status_code
            return
        numbers = tickets.pyquery('.ticket-number-plain a')
        assert set(item.text() for item in numbers.items()) == set(visible)

    # admins should always be able to see everything
    assert_visible_tickets('admin', ticket_nrs.values())
    for group_name in groups:
        assert_visible_tickets(f'{group_name}-admin', ticket_nrs.values())

    # supporters/editors should only see what they have access to
    assert_visible_tickets('editor', [
        ticket_nrs['EVN'],
        ticket_nrs['RSV'],
    ])
    assert_visible_tickets('supporter', [
        ticket_nrs['EVN'],
        ticket_nrs['RSV'],
    ])

    assert_visible_tickets('Steueramt-editor', [
        ticket_nrs['EVN'],
        ticket_nrs['FRM-S'],
        ticket_nrs['RSV'],
    ])
    assert_visible_tickets('Steueramt-supporter', [
        ticket_nrs['EVN'],
        ticket_nrs['FRM-S'],
        ticket_nrs['RSV'],
    ])

    assert_visible_tickets('HR-editor', [
        ticket_nrs['EVN'],
        ticket_nrs['PER'],
        ticket_nrs['RSV'],
    ])
    assert_visible_tickets('HR-supporter', [
        ticket_nrs['EVN'],
        ticket_nrs['PER'],
        ticket_nrs['RSV'],
    ])

    assert_visible_tickets('HR+Steueramt-editor', [
        ticket_nrs['EVN'],
        ticket_nrs['PER'],
        ticket_nrs['FRM-S'],
        ticket_nrs['RSV'],
    ])
    assert_visible_tickets('HR+Steueramt-supporter', [
        ticket_nrs['EVN'],
        ticket_nrs['PER'],
        ticket_nrs['FRM-S'],
        ticket_nrs['RSV'],
    ])

    assert_visible_tickets('Sekretariat-editor', [
        ticket_nrs['EVN'],
        ticket_nrs['FRM-S'],
        ticket_nrs['FRM-W'],
        ticket_nrs['RSV'],
        ticket_nrs['RSV-A'],
    ])
    assert_visible_tickets('Sekretariat-supporter', [
        ticket_nrs['EVN'],
        ticket_nrs['FRM-S'],
        ticket_nrs['FRM-W'],
        ticket_nrs['RSV'],
        ticket_nrs['RSV-A'],
    ])


    # filtering should work correctly regardless of access
    assert_visible_tickets('admin', [ticket_nrs['EVN']], 'EVN')
    for group_name in groups:
        assert_visible_tickets(f'{group_name}-admin', [
            ticket_nrs['EVN'],
        ], 'EVN')

    assert_visible_tickets('editor', [ticket_nrs['EVN']], 'EVN')
    assert_visible_tickets('supporter', [ticket_nrs['EVN']], 'EVN')

    assert_visible_tickets('Steueramt-editor', [ticket_nrs['EVN']], 'EVN')
    assert_visible_tickets('Steueramt-supporter', [ticket_nrs['EVN']], 'EVN')

    assert_visible_tickets('HR-editor', [ticket_nrs['EVN']], 'EVN')
    assert_visible_tickets('HR-supporter', [ticket_nrs['EVN']], 'EVN')

    assert_visible_tickets('HR+Steueramt-editor', [ticket_nrs['EVN']], 'EVN')
    assert_visible_tickets('HR+Steueramt-supporter', [
        ticket_nrs['EVN'],
    ], 'EVN')

    assert_visible_tickets('Sekretariat-editor', [ticket_nrs['EVN']], 'EVN')
    assert_visible_tickets('Sekretariat-supporter', [ticket_nrs['EVN']], 'EVN')

    assert_visible_tickets('admin', [
        ticket_nrs['FRM-S'],
        ticket_nrs['FRM-W'],
    ], 'FRM')
    for group_name in groups:
        assert_visible_tickets(f'{group_name}-admin', [
            ticket_nrs['FRM-S'],
            ticket_nrs['FRM-W'],
        ], 'FRM')


    assert_visible_tickets('editor', [], 'FRM')
    assert_visible_tickets('supporter', [], 'FRM')

    assert_visible_tickets('Steueramt-editor', [ticket_nrs['FRM-S']], 'FRM')
    assert_visible_tickets('Steueramt-supporter', [ticket_nrs['FRM-S']], 'FRM')

    assert_visible_tickets('HR-editor', [], 'FRM')
    assert_visible_tickets('HR-supporter', [], 'FRM')

    assert_visible_tickets('HR+Steueramt-editor', [ticket_nrs['FRM-S']], 'FRM')
    assert_visible_tickets('HR+Steueramt-supporter', [
        ticket_nrs['FRM-S'],
    ], 'FRM')

    assert_visible_tickets('Sekretariat-editor', [
        ticket_nrs['FRM-S'],
        ticket_nrs['FRM-W'],
    ], 'FRM')
    assert_visible_tickets('Sekretariat-supporter', [
        ticket_nrs['FRM-S'],
        ticket_nrs['FRM-W'],
    ], 'FRM')


    assert_visible_tickets('admin', [ticket_nrs['PER']], 'PER')
    for group_name in groups:
        assert_visible_tickets(f'{group_name}-admin', [
            ticket_nrs['PER'],
        ], 'PER')

    assert_visible_tickets('editor', [], 'PER')
    assert_visible_tickets('supporter', [], 'PER')

    assert_visible_tickets('Steueramt-editor', [], 'PER')
    assert_visible_tickets('Steueramt-supporter', [], 'PER')

    assert_visible_tickets('HR-editor', [ticket_nrs['PER']], 'PER')
    assert_visible_tickets('HR-supporter', [ticket_nrs['PER']], 'PER')

    assert_visible_tickets('HR+Steueramt-editor', [ticket_nrs['PER']], 'PER')
    assert_visible_tickets('HR+Steueramt-supporter', [
        ticket_nrs['PER'],
    ], 'PER')

    assert_visible_tickets('Sekretariat-editor', [], 'PER')
    assert_visible_tickets('Sekretariat-supporter', [], 'PER')


    assert_visible_tickets('admin', [
        ticket_nrs['RSV'],
        ticket_nrs['RSV-A'],
    ], 'RSV')
    for group_name in groups:
        assert_visible_tickets(f'{group_name}-admin', [
            ticket_nrs['RSV'],
            ticket_nrs['RSV-A'],
        ], 'RSV')

    assert_visible_tickets('editor', [ticket_nrs['RSV']], 'RSV')
    assert_visible_tickets('supporter', [ticket_nrs['RSV']], 'RSV')

    assert_visible_tickets('Steueramt-editor', [ticket_nrs['RSV']], 'RSV')
    assert_visible_tickets('Steueramt-supporter', [ticket_nrs['RSV']], 'RSV')

    assert_visible_tickets('HR-editor', [ticket_nrs['RSV']], 'RSV')
    assert_visible_tickets('HR-supporter', [ticket_nrs['RSV']], 'RSV')

    assert_visible_tickets('HR+Steueramt-editor', [ticket_nrs['RSV']], 'RSV')
    assert_visible_tickets('HR+Steueramt-supporter', [
        ticket_nrs['RSV'],
    ], 'RSV')

    assert_visible_tickets('Sekretariat-editor', [
        ticket_nrs['RSV'],
        ticket_nrs['RSV-A'],
    ], 'RSV')
    assert_visible_tickets('Sekretariat-supporter', [
        ticket_nrs['RSV'],
        ticket_nrs['RSV-A'],
    ], 'RSV')


    # members/anonymous users should not have access to this view
    assert_visible_tickets('member', [], status=403)
    assert_visible_tickets('anonymous', [], status=403)
    for group_name in groups:
        assert_visible_tickets(f'{group_name}-member', [], status=403)
        assert_visible_tickets(f'{group_name}-anonymous', [], status=403)
