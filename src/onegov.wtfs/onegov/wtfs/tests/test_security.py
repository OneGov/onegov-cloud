from datetime import date
from morepath import Identity
from onegov.core.security import Public
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import ScanJob
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted
from onegov.wtfs.security import ViewModel
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

    municipality_id = uuid4()
    session.add(Municipality(
        id=municipality_id,
        name='Municipality A',
        bfs_number=10,
        group_id=group_a_id
    ))
    session.add(PickupDate(
        date=date.today(),
        municipality_id=municipality_id,
    ))
    session.add(ScanJob(
        type='normal',
        group_id=group_a_id,
        municipality_id=municipality_id,
        dispatch_date=date(2019, 1, 1))
    )

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
    municipality = session.query(Municipality).one()
    scan_job = session.query(ScanJob).one()

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
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)

    # UserGroupCollection
    model = UserGroupCollection(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)

    # UserGroup
    for user in (admin, admin_a, admin_b):
        for model in (group_a, group_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
        for model in (group, ):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        for model in (group_a, group_b, group):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)

    # UserCollection
    model = UserCollection(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (editor, editor_a, editor_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)

    # User
    for user in (admin, admin_a, admin_b):
        for model in (admin, admin_a, admin_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
        for model in (editor, editor_a, editor_b, member, member_a, member_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
    for user in (editor, ):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_a, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
    for user in (editor_a, ):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
        for model in (member_a,):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
    for user in (editor_b, ):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_a):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
        for model in (member_b,):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
    for user in (member, member_a, member_b):
        for model in (admin, admin_a, admin_b, editor, editor_a, editor_b,
                      member, member_a, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)

    # MunicipalityCollection
    model = MunicipalityCollection(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)

    # Municipality
    for user in (admin, admin_a, admin_b):
        for model in (municipality,):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
        for model in (Municipality(),):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        for model in (municipality, Municipality()):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)

    # ScanJobCollection
    model = ScanJobCollection(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (editor_a, editor_b, member_a, member_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (editor, member):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)

    # ScanJob
    model = scan_job
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
    for user in (editor, editor_b, member, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
    for user in (editor_a, member_a):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)

    # DailyList
    daily_list_b = DailyList(session, type_='boxes')
    daily_list_f = DailyList(session, type_='forms')
    for user in (admin, admin_a, admin_b):
        for model in (daily_list_b, daily_list_f):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
    for user in (editor, editor_a, editor_b, member_a, member_b):
        for model in (daily_list_b, daily_list_f):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
    for user in (member,):
        for model in (daily_list_b,):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
        for model in (daily_list_f,):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
