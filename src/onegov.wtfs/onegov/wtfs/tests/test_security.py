from morepath import Identity
from onegov.core.security import Personal
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security import Secret
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.models import Municipality
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelSameGroup
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import DeleteModelSameGroup
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelSameGroup
from onegov.wtfs.security import ViewModel
from onegov.wtfs.security import ViewModelSameGroup
from uuid import uuid4


def test_permissions(wtfs_app, wtfs_password):
    session = wtfs_app.session()

    # Remove existing group
    session.query(User).filter_by(realname='Editor').one().group_id = None
    session.query(User).filter_by(realname='Member').one().group_id = None
    session.query(UserGroup).delete()

    # Add new
    group_a_id = uuid4()
    session.add(UserGroup(id=group_a_id, name="Group A"))
    session.add(User(
        realname='Admin A',
        username='admin-a@example.org',
        password_hash=wtfs_password,
        role='admin',
        group_id=group_a_id
    ))
    session.add(User(
        realname='Editor A',
        username='editor-a@example.org',
        password_hash=wtfs_password,
        role='editor',
        group_id=group_a_id
    ))
    session.add(User(
        realname='Member A',
        username='member-a@example.org',
        password_hash=wtfs_password,
        role='member',
        group_id=group_a_id
    ))

    group_b_id = uuid4()
    session.add(UserGroup(id=group_b_id, name="Group B"))
    session.add(User(
        realname='Admin B',
        username='admin-b@example.org',
        password_hash=wtfs_password,
        role='admin',
        group_id=group_b_id
    ))
    session.add(User(
        realname='Editor B',
        username='editor-b@example.org',
        password_hash=wtfs_password,
        role='editor',
        group_id=group_b_id
    ))
    session.add(User(
        realname='Member B',
        username='member-b@example.org',
        password_hash=wtfs_password,
        role='member',
        group_id=group_b_id
    ))

    group_m_id = uuid4()
    session.add(UserGroup(id=group_m_id, name="Group M"))
    session.add(Municipality(
        name='Municipality A',
        bfs_number=10,
        group_id=group_m_id
    ))

    admin = session.query(User).filter_by(realname='Admin').one()
    admin_a = session.query(User).filter_by(realname='Admin A').one()
    admin_b = session.query(User).filter_by(realname='Admin B').one()
    editor = session.query(User).filter_by(realname='Editor').one()
    editor_a = session.query(User).filter_by(realname='Editor A').one()
    editor_b = session.query(User).filter_by(realname='Editor B').one()
    member = session.query(User).filter_by(realname='Member').one()
    member_a = session.query(User).filter_by(realname='Member A').one()
    member_b = session.query(User).filter_by(realname='Member B').one()
    group = UserGroup()
    group_a = session.query(UserGroup).filter_by(name='Group A').one()
    group_b = session.query(UserGroup).filter_by(name='Group B').one()
    group_m = session.query(UserGroup).filter_by(name='Group M').one()

    def permits(user, model, permission):
        return wtfs_app._permits(
            Identity(
                userid=user.username,
                groupid=user.group_id.hex if user.group_id else '',
                role=user.role,
                application_id=wtfs_app.application_id
            ),
            model,
            permission
        )

    # General
    model = object()
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Secret)
        assert permits(user, model, Private)
        assert permits(user, model, Personal)
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, EditModel)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert not permits(user, model, ViewModelSameGroup)
    for user in (editor, editor_a, editor_b):
        assert not permits(user, model, Secret)
        assert permits(user, model, Private)
        assert permits(user, model, Personal)
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert not permits(user, model, ViewModelSameGroup)
    for user in (member, member_a, member_b):
        assert not permits(user, model, Secret)
        assert not permits(user, model, Private)
        assert permits(user, model, Personal)
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert not permits(user, model, ViewModelSameGroup)

    # UserGroupCollection
    model = UserGroupCollection(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Secret)
        assert permits(user, model, Private)
        assert permits(user, model, Personal)
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, EditModel)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert not permits(user, model, ViewModelSameGroup)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert not permits(user, model, Secret)
        assert not permits(user, model, Private)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert not permits(user, model, ViewModelSameGroup)

    # UserGroup
    for user in (admin, admin_a, admin_b):
        for model in (group_a, group_b, group_m):
            assert permits(user, model, Secret)
            assert permits(user, model, Private)
            assert permits(user, model, Personal)
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)
        for model in (group, ):
            assert permits(user, model, Secret)
            assert permits(user, model, Private)
            assert permits(user, model, Personal)
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, EditModel)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        for model in (group_a, group_b, group_m, group):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)

    # UserCollection
    model = UserCollection(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Secret)
        assert permits(user, model, Private)
        assert permits(user, model, Personal)
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, EditModel)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert permits(user, model, ViewModelSameGroup)
    for user in (editor, editor_a, editor_b):
        assert not permits(user, model, Secret)
        assert not permits(user, model, Private)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert permits(user, model, ViewModelSameGroup)
    for user in (member, member_a, member_b):
        assert not permits(user, model, Secret)
        assert not permits(user, model, Private)
        assert not permits(user, model, Personal)
        assert not permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, AddModelSameGroup)
        assert not permits(user, model, EditModelSameGroup)
        assert not permits(user, model, DeleteModelSameGroup)
        assert not permits(user, model, ViewModelSameGroup)

    # User
    for user in (admin, admin_a, admin_b):
        for model in (admin, admin_a, admin_b):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)
        for model in (editor, editor_a, editor_b, member, member_a, member_b):
            assert permits(user, model, Secret)
            assert permits(user, model, Private)
            assert permits(user, model, Personal)
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, EditModel)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert permits(user, model, DeleteModelSameGroup)
            assert permits(user, model, ViewModelSameGroup)
    for user in (editor, ):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_a, member_b):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)
    for user in (editor_a, ):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_b):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)
        for model in (member_a,):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert permits(user, model, EditModelSameGroup)
            assert permits(user, model, DeleteModelSameGroup)
            assert permits(user, model, ViewModelSameGroup)
    for user in (editor_b, ):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_a):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)
        for model in (member_b,):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert permits(user, model, EditModelSameGroup)
            assert permits(user, model, DeleteModelSameGroup)
            assert permits(user, model, ViewModelSameGroup)
    for user in (member, member_a, member_b):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_a, member_b):
            assert not permits(user, model, Secret)
            assert not permits(user, model, Private)
            assert not permits(user, model, Personal)
            assert not permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, AddModelSameGroup)
            assert not permits(user, model, EditModelSameGroup)
            assert not permits(user, model, DeleteModelSameGroup)
            assert not permits(user, model, ViewModelSameGroup)

    # todo: Municipality
    # todo: MunicipalityCollection
    # todo: split up tests
