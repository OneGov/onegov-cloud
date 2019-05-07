from datetime import date
from morepath import Identity
from onegov.core.security import Public
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import UserGroup
from onegov.user import UserGroupCollection
from onegov.wtfs.collections import MunicipalityCollection
from onegov.wtfs.collections import PaymentTypeCollection
from onegov.wtfs.collections import ScanJobCollection
from onegov.wtfs.models import DailyList
from onegov.wtfs.models import DailyListBoxes
from onegov.wtfs.models import DailyListBoxesAndForms
from onegov.wtfs.models import Invoice
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import Notification
from onegov.wtfs.models import PaymentType
from onegov.wtfs.models import PickupDate
from onegov.wtfs.models import Report
from onegov.wtfs.models import ReportBoxes
from onegov.wtfs.models import ReportBoxesAndForms
from onegov.wtfs.models import ReportFormsByMunicipality
from onegov.wtfs.models import ScanJob
from onegov.wtfs.models import UserManual
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import AddModelUnrestricted
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import EditModelUnrestricted
from onegov.wtfs.security import ViewModel
from onegov.wtfs.security import ViewModelUnrestricted
from uuid import uuid4


def test_permissions(wtfs_app, wtfs_password):
    session = wtfs_app.session()

    # Remove existing users and group
    session.query(User).filter_by(realname='Editor').one().group_id = None
    session.query(User).filter_by(realname='Member').one().group_id = None
    session.query(Municipality).delete()

    # Add new
    municipality_a_id = uuid4()
    session.add(Municipality(
        id=municipality_a_id,
        name='Municipality A',
        bfs_number=10,
    ))
    session.add(PickupDate(
        date=date.today(),
        municipality_id=municipality_a_id,
    ))
    session.add(ScanJob(
        type='normal',
        municipality_id=municipality_a_id,
        delivery_number=1,
        dispatch_date=date(2019, 1, 1))
    )
    session.add(User(
        realname='Admin A',
        username='admin-a@example.org',
        password_hash=wtfs_password,
        role='admin',
        group_id=municipality_a_id
    ))
    session.add(User(
        realname='Editor A',
        username='editor-a@example.org',
        password_hash=wtfs_password,
        role='editor',
        group_id=municipality_a_id
    ))
    session.add(User(
        realname='Member A',
        username='member-a@example.org',
        password_hash=wtfs_password,
        role='member',
        group_id=municipality_a_id
    ))

    municipality_b_id = uuid4()
    session.add(Municipality(
        id=municipality_b_id,
        name='Municipality B',
        bfs_number=20,
    ))
    session.add(User(
        realname='Admin B',
        username='admin-b@example.org',
        password_hash=wtfs_password,
        role='admin',
        group_id=municipality_b_id
    ))
    session.add(User(
        realname='Editor B',
        username='editor-b@example.org',
        password_hash=wtfs_password,
        role='editor',
        group_id=municipality_b_id
    ))
    session.add(User(
        realname='Member B',
        username='member-b@example.org',
        password_hash=wtfs_password,
        role='member',
        group_id=municipality_b_id
    ))

    query = session.query
    admin = query(User).filter_by(realname='Admin').one()
    admin_a = query(User).filter_by(realname='Admin A').one()
    admin_b = query(User).filter_by(realname='Admin B').one()
    editor = query(User).filter_by(realname='Editor').one()
    editor_a = query(User).filter_by(realname='Editor A').one()
    editor_b = query(User).filter_by(realname='Editor B').one()
    member = query(User).filter_by(realname='Member').one()
    member_a = query(User).filter_by(realname='Member A').one()
    member_b = query(User).filter_by(realname='Member B').one()
    group = UserGroup()
    group_a = query(UserGroup).filter_by(name='Municipality A').one()
    group_b = query(UserGroup).filter_by(name='Municipality B').one()
    municipality = Municipality()
    municipality_a = query(Municipality).filter_by(name='Municipality A').one()
    municipality_b = query(Municipality).filter_by(name='Municipality B').one()
    scan_job = query(ScanJob).one()

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
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

    # UserGroupCollection / MunicipalityCollection
    # MunicipalityCollection
    for model in (
        MunicipalityCollection(session),
        UserGroupCollection(session)
    ):
        for user in (admin, admin_a, admin_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
        for user in (editor, editor_a, editor_b, member, member_a, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)

    # UserGroup / Municipality
    for user in (admin, admin_a, admin_b):
        for model in (group_a, group_b, municipality_a, municipality_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
        for model in (group, municipality):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        for model in (
            group_a, group_b, group,
            municipality_a, municipality_b, municipality
        ):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)

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
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)
    for user in (member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

    # User
    for user in (admin, admin_a, admin_b):
        for model in (admin, admin_a, admin_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            if user == model:
                assert not permits(user, model, DeleteModel)
            else:
                assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
        for model in (editor, editor_a, editor_b, member, member_a, member_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, ):
        for model in (admin, admin_a, admin_b, editor_a, editor_b,
                      member, member_a, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
    for user in (editor, ):
        for model in (editor, ):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
    for user in (editor_a, ):
        for model in (admin, admin_a, admin_b, editor, editor_b,
                      member, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
        for model in (editor_a, ):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
        for model in (member_a,):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
    for user in (editor_b, ):
        for model in (admin, admin_a, admin_b, editor, editor_a,
                      member, member_a):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
        for model in (editor_b, ):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
        for model in (member_b,):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
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
            assert not permits(user, model, ViewModelUnrestricted)

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
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor_a, editor_b, member_a, member_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)
    for user in (editor, member):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

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
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_b, member, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)
    for user in (editor_a, member_a):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

    # DailyList
    for model in (DailyList(), DailyListBoxes(session)):
        for user in (admin, admin_a, admin_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
        for user in (editor, editor_a, editor_b, member_a, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
        for user in (member,):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)
    for model in (DailyListBoxesAndForms(session), ):
        for user in (admin, admin_a, admin_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
        for user in (editor, editor_a, editor_b, member, member_a, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)

    # Report
    for model in (
        Report(session),
        ReportBoxes(session),
        ReportBoxesAndForms(session),
        ReportFormsByMunicipality(session)
    ):
        for user in (admin, admin_a, admin_b):
            assert permits(user, model, Public)
            assert permits(user, model, AddModel)
            assert permits(user, model, AddModelUnrestricted)
            assert permits(user, model, EditModel)
            assert permits(user, model, EditModelUnrestricted)
            assert permits(user, model, DeleteModel)
            assert permits(user, model, ViewModel)
            assert permits(user, model, ViewModelUnrestricted)
        for user in (editor, editor_a, editor_b, member, member_a, member_b):
            assert permits(user, model, Public)
            assert not permits(user, model, AddModel)
            assert not permits(user, model, AddModelUnrestricted)
            assert not permits(user, model, EditModel)
            assert not permits(user, model, EditModelUnrestricted)
            assert not permits(user, model, DeleteModel)
            assert not permits(user, model, ViewModel)
            assert not permits(user, model, ViewModelUnrestricted)

    # Notification
    model = Notification()
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

    # Invoice
    model = Invoice(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

    # PaymentType
    model = PaymentType()
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

    # PaymentTypeCollection
    model = PaymentTypeCollection(session)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert not permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)

    # UserManual
    model = UserManual(wtfs_app)
    for user in (admin, admin_a, admin_b):
        assert permits(user, model, Public)
        assert permits(user, model, AddModel)
        assert permits(user, model, AddModelUnrestricted)
        assert permits(user, model, EditModel)
        assert permits(user, model, EditModelUnrestricted)
        assert permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert permits(user, model, ViewModelUnrestricted)
    for user in (editor, editor_a, editor_b, member, member_a, member_b):
        assert permits(user, model, Public)
        assert not permits(user, model, AddModel)
        assert not permits(user, model, AddModelUnrestricted)
        assert not permits(user, model, EditModel)
        assert not permits(user, model, EditModelUnrestricted)
        assert not permits(user, model, DeleteModel)
        assert permits(user, model, ViewModel)
        assert not permits(user, model, ViewModelUnrestricted)
