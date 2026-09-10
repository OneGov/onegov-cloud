from __future__ import annotations

import pytest
from onegov.user.auth.provider import RolesMapping


class MockApp:
    def __init__(self, application_id: str, namespace: str) -> None:
        self.application_id = application_id
        self.namespace = namespace


@pytest.fixture
def roles_mapping() -> RolesMapping:
    roles = {
        '__default__': {
            'admins': 'default_admins',
            'editors': 'default_editors',
            'supporters': 'default_supporters',
            'members': 'default_members',
        },
        'onegov_org': {
            'admins': 'org_admins',
            'editors': 'org_editors',
            'supporters': 'org_supporters',
            'members': 'org_members',
        },
        'onegov_org/govikon': {
            'admins': 'govikon_admins',
            'editors': 'govikon_editors',
            'supporters': 'govikon_supporters',
            'members': 'govikon_members',
        },
        'onegov_town6/casetown': {
            'admins': 'CaseTown_Admins',
            'editors': 'CaseTown_Editors',
            'supporters': 'CaseTown_Supporters',
            'members': 'CaseTown_Members',
        },
    }
    return RolesMapping(roles)


def test_app_specific(roles_mapping: RolesMapping) -> None:
    app = MockApp('onegov_org/govikon', 'onegov_org')
    assert roles_mapping.app_specific(app) == {
        'admins': 'govikon_admins',
        'editors': 'govikon_editors',
        'supporters': 'govikon_supporters',
        'members': 'govikon_members',
    }

    app = MockApp('onegov_org/govikon', 'unknown_namespace')
    assert roles_mapping.app_specific(app) == {
        'admins': 'govikon_admins',
        'editors': 'govikon_editors',
        'supporters': 'govikon_supporters',
        'members': 'govikon_members',
    }

    app = MockApp('unknown_app', 'onegov_org')
    assert roles_mapping.app_specific(app) == {
        'admins': 'org_admins',
        'editors': 'org_editors',
        'supporters': 'org_supporters',
        'members': 'org_members',
    }

    app = MockApp('unknown_app', 'unknown_namespace')
    assert roles_mapping.app_specific(app) == {
        'admins': 'default_admins',
        'editors': 'default_editors',
        'supporters': 'default_supporters',
        'members': 'default_members',
    }


def test_match(roles_mapping: RolesMapping) -> None:
    roles = roles_mapping.roles['__default__']

    groups = ['unknown_group']
    assert roles_mapping.match(roles, groups) is None

    groups = ['unknown_group', 'default_members']
    assert roles_mapping.match(roles, groups) == 'member'

    groups = ['default_admins', 'default_editors']
    assert roles_mapping.match(roles, groups) == 'admin'

    groups = ['default_editors', 'default_admins']
    assert roles_mapping.match(roles, groups) == 'admin'

    roles = roles_mapping.roles['onegov_org/govikon']
    groups = ['govikon_supporters', 'govikon_editors']
    assert roles_mapping.match(roles, groups) == 'editor'

    # ensure match is case-insensitive
    roles = roles_mapping.roles['onegov_town6/casetown']
    groups = ['CASEtown_Admins', 'CaseTown_Editors']
    assert roles_mapping.match(roles, groups) == 'admin'


def test_match_multiple_groups() -> None:
    roles: dict[str, str | list[str]] = {
        'admins': ['primary_admins', 'secondary_admins'],
        'editors': 'editors',
    }
    roles_mapping = RolesMapping({'__default__': roles})

    assert roles_mapping.match(roles, ['primary_admins']) == 'admin'
    assert roles_mapping.match(roles, ['SECONDARY_ADMINS']) == 'admin'
    assert roles_mapping.match(roles, ['editors']) == 'editor'
    assert roles_mapping.match(roles, ['unknown_group']) is None
