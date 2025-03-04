from morepath import Identity
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.ticket import Ticket
from onegov.ticket import TicketPermission
from onegov.user.models import User
from onegov.user.models import UserGroup


def test_security_ticket_permissions(org_app):
    session = org_app.session()

    # Remove existing users
    session.query(User).delete()

    # Create test data
    # ... user groups
    def create_group(name):
        result = UserGroup(name=name)
        session.add(result)
        return result

    groups = {
        'HR': create_group('HR'),
        'Steueramt': create_group('Steueramt'),
        'Sekretariat': create_group('Sekretariat')
    }

    # ... users
    def create_user(name, role, groups=None):
        result = User(
            realname=name,
            username=f'{name}@example.org',
            password_hash='hash',
            role=role,
            groups=groups or []
        )
        session.add(result)
        return result

    # TODO: Add a test case for multi-user-group-membership
    roles = ('admin', 'editor', 'member', 'anonymous')
    users = {}
    for role in roles:
        users[role] = create_user(role, role)
        for group in groups.values():
            name = f'{group.name}-{role}'
            users[name] = create_user(name, role, [group])

    # ... permissions
    def create_permission(handler_code, group, user_group):
        result = TicketPermission(
            handler_code=handler_code,
            group=group,
            user_group=user_group
        )
        session.add(result)
        return result

    create_permission('PER', None, groups['HR'])
    create_permission('FRM', 'Steuererklärung', groups['Steueramt'])
    create_permission('FRM', None, groups['Sekretariat'])

    # ... tickets
    def create_ticket(handler_code, group=''):
        result = Ticket(
            number=f'{handler_code}-{group}-1',
            title=f'{handler_code}-{group}',
            group=group,
            handler_code=handler_code,
            handler_id=f'{handler_code}-{group}'
        )
        session.add(result)
        return result

    tickets = {
        'EVN': create_ticket('EVN'),
        'PER': create_ticket('PER'),
        'FRM-S': create_ticket('FRM', 'Steuererklärung'),
        'FRM-W': create_ticket('FRM', 'Wohnsitzbestätigung'),
    }

    session.flush()

    # Test permissions

    def permits(user, model, permission):
        return org_app._permits(
            Identity(
                userid=user.username,
                groupid=frozenset(group.id.hex for group in user.groups),
                role=user.role,
                application_id=org_app.application_id
            ),
            model,
            permission
        )

    def assert_admin(user, model):
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert permits(user, model, Secret)

    def assert_editor(user, model):
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_member(user, model):
        assert permits(user, model, Public)
        assert permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    def assert_anonymous(user, model):
        assert permits(user, model, Public)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Private)
        assert not permits(user, model, Secret)

    # no permission defined
    ticket = tickets['EVN']
    assert_admin(users['admin'], ticket)
    assert_editor(users['editor'], ticket)
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group in groups:
        assert_admin(users[f'{group}-admin'], ticket)
        assert_editor(users[f'{group}-editor'], ticket)
        assert_member(users[f'{group}-member'], ticket)
        assert_anonymous(users[f'{group}-anonymous'], ticket)

    # globally exclude
    ticket = tickets['PER']
    assert_admin(users['admin'], ticket)
    assert_member(users['editor'], ticket)  # downgraded
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group in ('Sekretariat', 'Steueramt'):
        assert_admin(users[f'{group}-admin'], ticket)
        assert_member(users[f'{group}-editor'], ticket)  # downgraded
        assert_member(users[f'{group}-member'], ticket)
        assert_anonymous(users[f'{group}-anonymous'], ticket)
    assert_admin(users['HR-admin'], ticket)
    assert_member(users['HR-editor'], ticket)
    assert_member(users['HR-member'], ticket)
    assert_anonymous(users['HR-anonymous'], ticket)

    # specifically exclude
    ticket = tickets['FRM-S']
    assert_admin(users['admin'], ticket)
    assert_member(users['editor'], ticket)  # downgraded
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group in ('Sekretariat', 'HR'):
        assert_admin(users[f'{group}-admin'], ticket)
        assert_member(users[f'{group}-editor'], ticket)  # downgraded
        assert_member(users[f'{group}-member'], ticket)
        assert_anonymous(users[f'{group}-anonymous'], ticket)
    assert_admin(users['Steueramt-admin'], ticket)
    assert_member(users['Steueramt-editor'], ticket)
    assert_member(users['Steueramt-member'], ticket)
    assert_anonymous(users['Steueramt-anonymous'], ticket)

    ticket = tickets['FRM-W']
    assert_admin(users['admin'], ticket)
    assert_member(users['editor'], ticket)  # downgraded
    assert_member(users['member'], ticket)
    assert_anonymous(users['anonymous'], ticket)
    for group in ('Steueramt', 'HR'):
        assert_admin(users[f'{group}-admin'], ticket)
        assert_member(users[f'{group}-editor'], ticket)  # downgraded
        assert_member(users[f'{group}-member'], ticket)
        assert_anonymous(users[f'{group}-anonymous'], ticket)
    assert_admin(users['Sekretariat-admin'], ticket)
    assert_member(users['Sekretariat-editor'], ticket)
    assert_member(users['Sekretariat-member'], ticket)
    assert_anonymous(users['Sekretariat-anonymous'], ticket)
