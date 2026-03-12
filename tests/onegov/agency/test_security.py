from __future__ import annotations

from morepath import Identity
from morepath.authentication import NO_IDENTITY
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.models import AgencyMembershipMoveWithinAgency
from onegov.agency.models import AgencyMembershipMoveWithinPerson
from onegov.agency.models import AgencyMove
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson
from onegov.agency.models.ticket import AgencyMutationTicket
from onegov.agency.models.ticket import PersonMutationTicket
from onegov.agency.security import get_current_role
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.user.models import RoleMapping
from onegov.user.models import User
from onegov.user.models import UserGroup


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency import AgencyApp
    from sqlalchemy.orm import Session


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


def test_security_get_current_role(session: Session) -> None:
    admin = Identity(
        application_id='test',
        uid='1',
        userid='admin@example.org',
        role='admin',
        groupids=frozenset()
    )
    editor = Identity(
        application_id='test',
        uid='2',
        userid='editor@example.org',
        role='editor',
        groupids=frozenset()
    )
    member = Identity(
        application_id='test',
        uid='3',
        userid='member@example.org',
        role='member',
        groupids=frozenset()
    )

    assert get_current_role(session, NO_IDENTITY) is None
    assert get_current_role(session, admin) == 'admin'
    assert get_current_role(session, editor) == 'editor'
    assert get_current_role(session, member) == 'member'

    group = UserGroup(name='group')
    session.add(group)
    session.flush()

    session.add(
        RoleMapping(
            group_id=group.id,
            content_type='agencies',
            content_id='1234',
            role='admin'
        )
    )
    session.flush()
    member.groupids = frozenset({group.id.hex})
    assert get_current_role(session, member) == 'member'

    session.add(
        RoleMapping(
            group_id=group.id,
            content_type='agencies',
            content_id='1234',
            role='editor'
        )
    )
    session.flush()
    assert get_current_role(session, member) == 'editor'


def test_security_permissions(agency_app: AgencyApp) -> None:
    session = agency_app.session()

    # Remove existing users
    session.query(User).delete()

    # Create test data
    names = ('a', 'b', 'b-1', 'b-2', 'b-2-1', 'b-2-2')
    roles = ('admin', 'editor', 'member', 'anonymous')

    # ... agencies
    agencies: dict[str, ExtendedAgency] = {}
    agn_tickets: dict[str, AgencyMutationTicket] = {}
    for name in names:
        agency = agencies.setdefault(
            name, ExtendedAgency(title=name, name=name)
        )
        session.add(agency)
        session.flush()

        agn_ticket = agn_tickets.setdefault(
            name,
            AgencyMutationTicket(
                title=f'AGN-{name}',
                number=f'AGN-{name}',
                group=f'AGN-{name}',
                handler_code='AGN',
                handler_id=f'AGN-{name}',
                handler_data={'handler_data': {'id': str(agency.id)}}
            )

        )
        session.add(agn_ticket)
        session.flush()
    agencies['b-1'].parent = agencies['b']
    agencies['b-2'].parent = agencies['b']
    agencies['b-2-1'].parent = agencies['b-2']
    agencies['b-2-2'].parent = agencies['b-2']

    # people & memberships
    people: dict[str, ExtendedPerson] = {}
    memberships = {}
    per_tickets: dict[str, PersonMutationTicket] = {}
    for name in names:
        person = people.setdefault(
            name, ExtendedPerson(first_name=name, last_name=name)
        )
        session.add(person)
        session.flush()

        agencies[name].add_person(person.id, name)
        memberships[name] = person.memberships.one()

        per_ticket = per_tickets.setdefault(
            name,
            PersonMutationTicket(
                title=f'PER-{name}',
                number=f'PER-{name}',
                group=f'PER-{name}',
                handler_code='PER',
                handler_id=f'PER-{name}',
                handler_data={'handler_data': {'id': str(person.id)}}
            )

        )
        session.add(per_ticket)
        session.flush()

    # ... groups
    groups: dict[str, UserGroup] = {}
    for role in roles:
        for name in names:
            group_name = f'{name}-{role}s'
            group = groups.setdefault(group_name, UserGroup(name=group_name))
            session.add(group)
            session.flush()
            session.add(
                RoleMapping(
                    group_id=group.id,
                    content_type='agencies',
                    content_id=str(agencies[name].id),
                    role=role
                )
            )

        # Add a group which spans over A-B
        group_name = f'a-b-{role}s'
        group = groups.setdefault(group_name, UserGroup(name=group_name))
        session.add(group)
        session.flush()
        session.add(
            RoleMapping(
                group_id=group.id,
                content_type='agencies',
                content_id=str(agencies['a'].id),
                role=role
            )
        )
        session.add(
            RoleMapping(
                group_id=group.id,
                content_type='agencies',
                content_id=str(agencies['b'].id),
                role=role
            )
        )
    session.flush()

    # ... users
    users = {}
    for role in roles:
        # global roles, e.g. 'editor'
        user = create_user(role, role)
        users[role] = user
        session.add(user)

        for name in names:
            # users with direct role mapping, e.g. 'a-editor'
            real_role = 'member' if role != 'anonymous' else 'anonymous'
            username = f'{name}-{role}'
            user = users.setdefault(username, create_user(username, real_role))
            session.add(user)
            session.add(
                RoleMapping(
                    username=user.username,
                    content_type='agencies',
                    content_id=str(agencies[name].id),
                    role=role
                )
            )

            # users with group role mapping, e.g. 'a-editor-1'
            for suffix in (1, 2):
                username = f'{name}-{role}-{suffix}'
                user = users.setdefault(username, create_user(
                    username,
                    real_role,
                    [groups[f'{name}-{role}s']]
                ))
                session.add(user)

        # users which span over A-B
        username = f'a-b-{role}'
        user = users.setdefault(username, create_user(
            username,
            role,
            [groups[f'a-b-{role}s']]
        ))
        session.add(user)
    session.flush()

    def permits(user: User, model: object, permission: object) -> bool:
        return agency_app._permits(
            Identity(
                uid=user.id.hex,
                userid=user.username,
                groupids=frozenset(group.id.hex for group in user.groups),
                role=user.role,
                application_id=agency_app.application_id
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

    # ExtendedAgency
    for name, agency in agencies.items():
        assert_admin(users['admin'], agency)
        assert_member(users[f'{name}-admin'], agency)
        assert_member(users[f'{name}-admin-1'], agency)
        assert_member(users[f'{name}-admin-2'], agency)
        assert_editor(users['editor'], agency)
        assert_member(users[f'{name}-editor'], agency)
        assert_editor(users[f'{name}-editor-1'], agency)  # elevated
        assert_editor(users[f'{name}-editor-2'], agency)  # elevated
        assert_member(users['member'], agency)
        assert_member(users[f'{name}-member'], agency)
        assert_member(users[f'{name}-member-1'], agency)
        assert_member(users[f'{name}-member-2'], agency)
        assert_anonymous(users['anonymous'], agency)
        assert_anonymous(users[f'{name}-anonymous'], agency)
        assert_anonymous(users[f'{name}-anonymous-1'], agency)
        assert_anonymous(users[f'{name}-anonymous-2'], agency)

    # ... traversal
    assert not permits(users['a-editor'], agencies['b-2-1'], Private)
    assert not permits(users['a-editor-1'], agencies['b-2-1'], Private)
    assert not permits(users['b-editor'], agencies['b-2-1'], Private)
    assert permits(users['b-editor-1'], agencies['b-2-1'], Private)
    assert not permits(users['b-2-editor'], agencies['b-2-1'], Private)
    assert permits(users['b-2-editor-1'], agencies['b-2-1'], Private)
    assert not permits(users['b-2-2-editor'], agencies['b-2-1'], Private)
    assert not permits(users['b-2-2-editor-1'], agencies['b-2-1'], Private)

    # ExtendedAgencyMembership
    for name, membership in memberships.items():
        assert_admin(users['admin'], membership)
        assert_member(users[f'{name}-admin'], membership)
        assert_member(users[f'{name}-admin-1'], membership)
        assert_member(users[f'{name}-admin-2'], membership)
        assert_editor(users['editor'], membership)
        assert_member(users[f'{name}-editor'], membership)
        assert_editor(users[f'{name}-editor-1'], membership)  # elevated
        assert_editor(users[f'{name}-editor-2'], membership)  # elevated
        assert_member(users['member'], membership)
        assert_member(users[f'{name}-member'], membership)
        assert_member(users[f'{name}-member-1'], membership)
        assert_member(users[f'{name}-member-2'], membership)
        assert_anonymous(users['anonymous'], membership)
        assert_anonymous(users[f'{name}-anonymous'], membership)
        assert_anonymous(users[f'{name}-anonymous-1'], membership)
        assert_anonymous(users[f'{name}-anonymous-2'], membership)

    # ... traversal
    assert not permits(users['a-editor'], memberships['b-2-1'], Private)
    assert not permits(users['a-editor-1'], memberships['b-2-1'], Private)
    assert not permits(users['b-editor'], memberships['b-2-1'], Private)
    assert permits(users['b-editor-1'], memberships['b-2-1'], Private)
    assert not permits(users['b-2-editor'], memberships['b-2-1'], Private)
    assert permits(users['b-2-editor-1'], memberships['b-2-1'], Private)
    assert not permits(users['b-2-2-editor'], memberships['b-2-1'], Private)
    assert not permits(users['b-2-2-editor-1'], memberships['b-2-1'], Private)

    # ExtendedPerson
    for name, person in people.items():
        assert_admin(users['admin'], person)
        assert_member(users[f'{name}-admin'], person)
        assert_member(users[f'{name}-admin-1'], person)
        assert_member(users[f'{name}-admin-2'], person)
        assert_editor(users['editor'], person)
        assert_member(users[f'{name}-editor'], person)
        assert_editor(users[f'{name}-editor-1'], person)  # elevated
        assert_editor(users[f'{name}-editor-2'], person)  # elevated
        assert_member(users['member'], person)
        assert_member(users[f'{name}-member'], person)
        assert_member(users[f'{name}-member-1'], person)
        assert_member(users[f'{name}-member-2'], person)
        assert_anonymous(users['anonymous'], person)
        assert_anonymous(users[f'{name}-anonymous'], person)
        assert_anonymous(users[f'{name}-anonymous-1'], person)
        assert_anonymous(users[f'{name}-anonymous-2'], person)

    # ... traversal
    assert not permits(users['a-editor'], people['b-2-1'], Private)
    assert not permits(users['a-editor-1'], people['b-2-1'], Private)
    assert not permits(users['b-editor'], people['b-2-1'], Private)
    assert permits(users['b-editor-1'], people['b-2-1'], Private)
    assert not permits(users['b-2-editor'], people['b-2-1'], Private)
    assert permits(users['b-2-editor-1'], people['b-2-1'], Private)
    assert not permits(users['b-2-2-editor'], people['b-2-1'], Private)
    assert not permits(users['b-2-2-editor-1'], people['b-2-1'], Private)

    # ... gain permission by adding a person
    assert not permits(users['a-editor'], people['b'], Private)
    assert not permits(users['a-editor-1'], people['b'], Private)
    agencies['a'].add_person(people['b'].id, 'b')
    assert not permits(users['a-editor'], people['b'], Private)
    assert permits(users['a-editor-1'], people['b'], Private)

    # ... person without memberships
    person = ExtendedPerson(first_name='1', last_name='1')
    assert permits(users['editor'], person, Private)
    assert not permits(users['a-editor'], person, Private)
    assert permits(users['a-editor-1'], person, Private)

    # ExtendedAgencyCollection
    model: object = ExtendedAgencyCollection(session)
    for name in names:
        assert_admin(users['admin'], model)
        assert_member(users[f'{name}-admin'], model)
        assert_member(users[f'{name}-admin-1'], model)
        assert_member(users[f'{name}-admin-2'], model)
        assert_editor(users['editor'], model)
        assert_member(users[f'{name}-editor'], model)
        assert_member(users[f'{name}-editor-1'], model)
        assert_member(users[f'{name}-editor-2'], model)
        assert_member(users['member'], model)
        assert_member(users[f'{name}-member'], model)
        assert_member(users[f'{name}-member-1'], model)
        assert_member(users[f'{name}-member-2'], model)
        assert_anonymous(users['anonymous'], model)
        assert_anonymous(users[f'{name}-anonymous'], model)
        assert_anonymous(users[f'{name}-anonymous-1'], model)
        assert_anonymous(users[f'{name}-anonymous-2'], model)

    # AgencyMove
    model = AgencyMove(
        session,
        subject_id=agencies['a'].id,
        target_id=agencies['b'].id,
        direction=None  # type: ignore[arg-type]
    )
    assert permits(users['admin'], model, Private)
    assert permits(users['a-b-admin'], model, Private)
    assert not permits(users['a-admin'], model, Private)
    assert not permits(users['a-admin-1'], model, Private)
    assert not permits(users['b-admin-2'], model, Private)
    assert permits(users['editor'], model, Private)
    assert permits(users['a-b-editor'], model, Private)
    assert not permits(users['a-editor'], model, Private)
    assert not permits(users['a-editor-1'], model, Private)
    assert not permits(users['b-editor-2'], model, Private)
    assert not permits(users['member'], model, Private)
    assert not permits(users['a-b-member'], model, Private)
    assert not permits(users['a-member'], model, Private)
    assert not permits(users['a-member-1'], model, Private)
    assert not permits(users['b-member-2'], model, Private)
    assert not permits(users['anonymous'], model, Private)
    assert not permits(users['a-b-anonymous'], model, Private)
    assert not permits(users['a-anonymous'], model, Private)
    assert not permits(users['a-anonymous-1'], model, Private)
    assert not permits(users['b-anonymous-2'], model, Private)

    # AgencyMembershipMoveWithinAgency
    model = AgencyMembershipMoveWithinAgency(
        session,
        memberships['a'].id,
        memberships['b'].id,
        'below'  # type: ignore[arg-type]
    )
    assert permits(users['admin'], model, Private)
    assert permits(users['a-b-admin'], model, Private)
    assert not permits(users['a-admin'], model, Private)
    assert not permits(users['a-admin-1'], model, Private)
    assert not permits(users['b-admin-2'], model, Private)
    assert permits(users['editor'], model, Private)
    assert permits(users['a-b-editor'], model, Private)
    assert not permits(users['a-editor'], model, Private)
    assert not permits(users['a-editor-1'], model, Private)
    assert not permits(users['b-editor-2'], model, Private)
    assert not permits(users['member'], model, Private)
    assert not permits(users['a-b-member'], model, Private)
    assert not permits(users['a-member'], model, Private)
    assert not permits(users['a-member-1'], model, Private)
    assert not permits(users['b-member-2'], model, Private)
    assert not permits(users['anonymous'], model, Private)
    assert not permits(users['a-b-anonymous'], model, Private)
    assert not permits(users['a-anonymous'], model, Private)
    assert not permits(users['a-anonymous-1'], model, Private)
    assert not permits(users['b-anonymous-2'], model, Private)

    # AgencyMembershipMoveWithinPerson
    model = AgencyMembershipMoveWithinPerson(
        session,
        memberships['a'].id,
        memberships['b'].id,
        'below'  # type: ignore[arg-type]
    )
    assert permits(users['admin'], model, Private)
    assert permits(users['a-b-admin'], model, Private)
    assert not permits(users['a-admin'], model, Private)
    assert not permits(users['a-admin-1'], model, Private)
    assert not permits(users['b-admin-2'], model, Private)
    assert permits(users['editor'], model, Private)
    assert permits(users['a-b-editor'], model, Private)
    assert not permits(users['a-editor'], model, Private)
    assert not permits(users['a-editor-1'], model, Private)
    assert not permits(users['b-editor-2'], model, Private)
    assert not permits(users['member'], model, Private)
    assert not permits(users['a-b-member'], model, Private)
    assert not permits(users['a-member'], model, Private)
    assert not permits(users['a-member-1'], model, Private)
    assert not permits(users['b-member-2'], model, Private)
    assert not permits(users['anonymous'], model, Private)
    assert not permits(users['a-b-anonymous'], model, Private)
    assert not permits(users['a-anonymous'], model, Private)
    assert not permits(users['a-anonymous-1'], model, Private)
    assert not permits(users['b-anonymous-2'], model, Private)

    # # AgencyMutationTicket
    for name, agn_ticket in agn_tickets.items():
        assert_admin(users['admin'], agn_ticket)
        assert_member(users[f'{name}-admin'], agn_ticket)
        assert_member(users[f'{name}-admin-1'], agn_ticket)
        assert_member(users[f'{name}-admin-2'], agn_ticket)
        assert_editor(users['editor'], agn_ticket)
        assert_member(users[f'{name}-editor'], agn_ticket)
        assert_editor(users[f'{name}-editor-1'], agn_ticket)  # elevated
        assert_editor(users[f'{name}-editor-2'], agn_ticket)  # elevated
        assert_member(users['member'], agn_ticket)
        assert_member(users[f'{name}-member'], agn_ticket)
        assert_member(users[f'{name}-member-1'], agn_ticket)
        assert_member(users[f'{name}-member-2'], agn_ticket)
        assert_anonymous(users['anonymous'], agn_ticket)
        assert_anonymous(users[f'{name}-anonymous'], agn_ticket)
        assert_anonymous(users[f'{name}-anonymous-1'], agn_ticket)
        assert_anonymous(users[f'{name}-anonymous-2'], agn_ticket)

    # ... traversal
    assert not permits(users['a-editor'], agn_tickets['b-2-1'], Private)
    assert not permits(users['a-editor-1'], agn_tickets['b-2-1'], Private)
    assert not permits(users['b-editor'], agn_tickets['b-2-1'], Private)
    assert permits(users['b-editor-1'], agn_tickets['b-2-1'], Private)
    assert not permits(users['b-2-editor'], agn_tickets['b-2-1'], Private)
    assert permits(users['b-2-editor-1'], agn_tickets['b-2-1'], Private)
    assert not permits(users['b-2-2-editor'], agn_tickets['b-2-1'], Private)
    assert not permits(users['b-2-2-editor-1'], agn_tickets['b-2-1'], Private)

    # PersonMutationTicket
    # ExtendedPerson
    for name, per_ticket in per_tickets.items():
        assert_admin(users['admin'], per_ticket)
        assert_member(users[f'{name}-admin'], per_ticket)
        assert_member(users[f'{name}-admin-1'], per_ticket)
        assert_member(users[f'{name}-admin-2'], per_ticket)
        assert_editor(users['editor'], per_ticket)
        assert_member(users[f'{name}-editor'], per_ticket)
        assert_editor(users[f'{name}-editor-1'], per_ticket)  # elevated
        assert_editor(users[f'{name}-editor-2'], per_ticket)  # elevated
        assert_member(users['member'], per_ticket)
        assert_member(users[f'{name}-member'], per_ticket)
        assert_member(users[f'{name}-member-1'], per_ticket)
        assert_member(users[f'{name}-member-2'], per_ticket)
        assert_anonymous(users['anonymous'], per_ticket)
        assert_anonymous(users[f'{name}-anonymous'], per_ticket)
        assert_anonymous(users[f'{name}-anonymous-1'], per_ticket)
        assert_anonymous(users[f'{name}-anonymous-2'], per_ticket)

    # ... traversal
    assert not permits(users['a-editor'], per_tickets['b-2-1'], Private)
    assert not permits(users['a-editor-1'], per_tickets['b-2-1'], Private)
    assert not permits(users['b-editor'], per_tickets['b-2-1'], Private)
    assert permits(users['b-editor-1'], per_tickets['b-2-1'], Private)
    assert not permits(users['b-2-editor'], per_tickets['b-2-1'], Private)
    assert permits(users['b-2-editor-1'], per_tickets['b-2-1'], Private)
    assert not permits(users['b-2-2-editor'], per_tickets['b-2-1'], Private)
    assert not permits(users['b-2-2-editor-1'], per_tickets['b-2-1'], Private)
