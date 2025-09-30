from datetime import date
from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.org.forms.commission_membership import CommissionMembershipAddForm
from onegov.org.forms.commission_membership import CommissionMembershipForm
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.collections import PASCommissionMembershipCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections import PASParliamentarianRoleCollection
from onegov.pas.collections import PASParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.pas.collections import RateSetCollection
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.forms import AttendenceAddCommissionForm
from onegov.pas.forms import AttendenceAddForm
from onegov.pas.forms import AttendenceAddPlenaryForm
from onegov.pas.forms import AttendenceForm
from onegov.pas.forms import PASParliamentarianRoleForm
from onegov.pas.forms import RateSetForm
from onegov.pas.forms import SettlementRunForm
from onegov.pas.models import RateSet
from onegov.pas.models import SettlementRun
from pytest import fixture
from tests.onegov.pas.conftest import DummyApp


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


@fixture(scope='function')
def dummy_request(session):
    return Bunch(
        app=Bunch(
            org=Bunch(
                geo_provider=None,
                open_files_target_blank=False
            ),
            schema='foo',
            sentry_dsn=None,
            version='1.0',
            websockets_client_url=lambda x: x,
            websockets_private_channel=None,
            session=lambda: session
        ),
        include=lambda x: x,
        is_manager=True,
        locale='de_CH',
        session=session,
        method='GET',  # not dynamic but doenst matter our purposess
        identity=Bunch(role='parliamentarian',
                       userid='test-user@example.com')  # same here
    )


@fixture(scope='function')
def dummy_admin_request(session):
    return Bunch(
        app=Bunch(
            org=Bunch(
                geo_provider=None,
                open_files_target_blank=False
            ),
            schema='foo',
            sentry_dsn=None,
            version='1.0',
            websockets_client_url=lambda x: x,
            websockets_private_channel=None,
            session=lambda: session
        ),
        include=lambda x: x,
        is_manager=True,
        is_admin=True,
        locale='de_CH',
        session=session,
        method='GET',  # not dynamic but doenst matter our purposess
        identity=Bunch(role='admin',
                       userid='admin@example.com')
    )


@freeze_time('2024-01-01')
def test_attendence_forms(session, dummy_admin_request):

    parliamentarians = PASParliamentarianCollection(DummyApp(session=session))
    parliamentarian = parliamentarians.add(
        first_name='a',
        last_name='b',
        email_primary='test-user@example.com'
    )
    parliamentarians.add(first_name='p', last_name='q')

    roles = PASParliamentarianRoleCollection(session)
    roles.add(parliamentarian_id=parliamentarian.id, end=date(2023, 1, 1))

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='x')
    commissions.add(name='y')
    commissions.add(name='z')

    # on request
    form = AttendenceForm()
    form.request = dummy_admin_request
    form.on_request()

    assert len(form.parliamentarian_id.choices) == 2
    assert len(form.commission_id.choices) == 4

    form = AttendenceAddForm()
    form.request = dummy_admin_request
    form.on_request()

    assert len(form.parliamentarian_id.choices) == 1

    # populate / get useful data
    form = AttendenceForm(DummyPostData({
        'commission_id': '',
        'duration': '2'
    }))

    assert form.get_useful_data()['commission_id'] is None
    assert form.get_useful_data()['duration'] == 120

    obj = Bunch()
    form.populate_obj(obj)
    assert obj.commission_id is None
    assert obj.duration == 120

    form = AttendenceForm(DummyPostData({
        'commission_id': commission.id,
        'duration': '2',
        'type': 'plenary'
    }))

    assert form.get_useful_data()['commission_id'] is None

    obj = Bunch()
    form.populate_obj(obj)
    assert obj.commission_id is None

    # ensure date
    form = AttendenceForm(DummyPostData({'date': '2024-01-01'}))
    form.request = dummy_admin_request
    form.on_request()
    assert not form.validate()
    assert form.errors['date'][0] == 'No within an active settlement run.'

    form = AttendenceAddForm(DummyPostData({'date': '2024-01-01'}))
    form.request = dummy_admin_request
    form.on_request()
    assert not form.validate()
    assert form.errors['date'][0] == 'No within an active settlement run.'

    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='2024',
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        active=True
    )

    assert not form.validate()
    assert 'date' not in form.errors

    settlement_run.active = False
    assert not form.validate()
    assert form.errors['date'][0] == 'No within an active settlement run.'

    settlement_run.active = True
    settlement_run.start = date(2024, 2, 2)
    assert not form.validate()
    assert form.errors['date'][0] == 'No within an active settlement run.'

    # ensure commission
    form = AttendenceForm(DummyPostData({
        'type': 'plenary',
        'parliamentarian_id': parliamentarian.id,
        'commission_id': commission.id
    }))
    form.request = dummy_admin_request
    form.on_request()
    assert not form.validate()
    assert 'commission_id' not in form.errors

    form = AttendenceForm(DummyPostData({
        'type': 'commission',
        'parliamentarian_id': parliamentarian.id,
        'commission_id': commission.id
    }))
    form.request = dummy_admin_request
    form.on_request()
    assert not form.validate()
    assert form.errors['commission_id'][0] == \
        'Parliamentarian is not in this commission.'

    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parliamentarian.id,
    )
    session.expire_all()
    assert not form.validate()
    assert 'commission_id' not in form.errors


@freeze_time('2024-01-01')
def test_add_plenary_attendence_form(session, dummy_request):
    parliamentarians = PASParliamentarianCollection(DummyApp(session=session))
    parliamentarian = parliamentarians.add(first_name='a', last_name='b')
    parliamentarians.add(first_name='p', last_name='q')

    roles = PASParliamentarianRoleCollection(session)
    roles.add(parliamentarian_id=parliamentarian.id, end=date(2023, 1, 1))

    # on request
    form = AttendenceAddPlenaryForm()
    form.request = dummy_request
    form.on_request()

    assert len(form.parliamentarian_id.choices) == 1
    assert len(form.parliamentarian_id.data) == 1

    # get useful data
    form = AttendenceAddPlenaryForm(DummyPostData({'duration': '2'}))
    assert form.get_useful_data()['duration'] == 120

    # ensure date (full test above)
    form = AttendenceAddCommissionForm(DummyPostData({'date': '2024-01-01'}))
    form.request = dummy_request
    assert not form.validate()
    assert form.errors['date'][0] == 'No within an active settlement run.'


@freeze_time('2024-01-01')
def test_add_commission_attendence_form(session, dummy_request):

    parliamentarians = PASParliamentarianCollection(DummyApp(session=session))
    parliamentarian = parliamentarians.add(first_name='a', last_name='b')
    parliamentarians.add(first_name='p', last_name='q')

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='x')

    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parliamentarian.id,
    )

    # on request
    form = AttendenceAddCommissionForm()
    form.request = dummy_request
    form.model = commission
    form.on_request()

    assert len(form.parliamentarian_id.choices) == 1
    assert len(form.parliamentarian_id.data) == 1

    # get useful data
    form = AttendenceAddCommissionForm(DummyPostData({'duration': '2'}))
    form.model = commission
    assert form.get_useful_data()['duration'] == 120
    assert form.get_useful_data()['commission_id'] == commission.id

    # ensure date (full test above)
    form = AttendenceAddCommissionForm(DummyPostData({'date': '2024-01-01'}))
    form.request = dummy_request
    assert not form.validate()
    assert form.errors['date'][0] == 'No within an active settlement run.'


@freeze_time('2024-01-01')
def test_commission_membership_forms(session, dummy_request):
    parliamentarians = PASParliamentarianCollection(DummyApp(session=session))
    parliamentarian = parliamentarians.add(first_name='a', last_name='b')
    parliamentarians.add(first_name='p', last_name='q')

    roles = PASParliamentarianRoleCollection(session)
    roles.add(parliamentarian_id=parliamentarian.id, end=date(2023, 1, 1))

    commissions = PASCommissionCollection(session)
    commissions.add(name='x')
    commissions.add(name='y')
    commissions.add(name='z')

    # on request
    form = CommissionMembershipForm()
    form.request = dummy_request
    form.on_request()

    assert len(form.parliamentarian_id.choices) == 2
    assert len(form.commission_id.choices) == 3

    form = CommissionMembershipAddForm()
    form.request = dummy_request
    form.on_request()

    assert len(form.parliamentarian_id.choices) == 1
    assert form.commission_id is None


def test_parliamentarian_role_form(session, dummy_request):
    parliamentarians = PASParliamentarianCollection(DummyApp(session=session))
    parliamentarians.add(first_name='p', last_name='q')

    groups = PASParliamentaryGroupCollection(session)
    groups.add(name='a')
    groups.add(name='b')
    groups.add(name='c')

    parties = PartyCollection(session)
    parties.add(name='x')
    parties.add(name='y')

    # on request
    form = PASParliamentarianRoleForm()
    form.request = dummy_request
    form.on_request()

    assert len(form.parliamentarian_id.choices) == 1
    assert len(form.parliamentary_group_id.choices) == 4
    assert len(form.party_id.choices) == 3

    # populate / get useful data
    form = PASParliamentarianRoleForm(DummyPostData({
        'parliamentary_group_id': '',
        'party_id': ''
    }))

    assert form.get_useful_data()['parliamentary_group_id'] is None
    assert form.get_useful_data()['party_id'] is None

    obj = Bunch()
    form.populate_obj(obj)
    assert obj.parliamentary_group_id is None
    assert obj.party_id is None


@freeze_time('2022-06-06')
def test_rate_set_form(session, dummy_request):
    collection = RateSetCollection(session)
    rate_set = collection.add(year=2020)

    # default year
    form = RateSetForm(DummyPostData())
    assert form.data['year'] == 2022

    # add
    form = RateSetForm(DummyPostData({'year': 2022}))
    form.model = collection
    form.request = dummy_request
    assert not form.validate()
    assert 'year' not in form.errors

    form = RateSetForm(DummyPostData({'year': 2020}))
    form.model = collection
    form.request = dummy_request
    assert not form.validate()
    assert form.errors['year'][0].interpolate() == \
        'Rate set for 2020 alredy exists'

    # edit
    form = RateSetForm(DummyPostData({'year': 2022}))
    form.model = RateSet(year=2021)
    form.request = dummy_request
    assert not form.validate()
    assert 'year' not in form.errors

    form = RateSetForm(DummyPostData({'year': 2020}))
    form.model = RateSet(year=2021)
    form.request = dummy_request
    assert not form.validate()
    assert form.errors['year'][0].interpolate() == \
        'Rate set for 2020 alredy exists'

    form = RateSetForm(DummyPostData({'year': 2020}))
    form.model = rate_set
    form.request = dummy_request
    assert not form.validate()
    assert 'year' not in form.errors


def test_settlement_run_form(session, dummy_request):
    collection = SettlementRunCollection(session)
    settlement_run = collection.add(
        name='2022',
        start=date(2022, 1, 1),
        end=date(2022, 12, 31),
        active=True
    )

    # range
    form = SettlementRunForm(DummyPostData({
        'start': '2021-01-01',
        'end': '2020-01-01',
    }))
    form.request = dummy_request
    assert not form.validate()
    assert form.errors['end'][0] == 'End must be after start'

    # add
    for start, end, overlaps in (
        ('2021-11-11', '2021-12-12', False),
        ('2021-12-12', '2022-02-02', True),
        ('2022-01-01', '2022-02-02', True),
        ('2022-02-02', '2022-04-04', True),
        ('2022-11-11', '2022-12-31', True),
        ('2023-01-01', '2023-02-02', False),
    ):
        form = SettlementRunForm(DummyPostData({'start': start, 'end': end}))
        form.model = collection
        form.request = dummy_request
        assert not form.validate()
        if overlaps:
            message = (
                'Dates overlap with existing settlement run: '
                '01.01.2022 - 31.12.2022'
            )
            assert form.errors['start'][0].interpolate() == message
            assert form.errors['end'][0].interpolate() == message
        else:
            assert 'start' not in form.errors
            assert 'end' not in form.errors

    # edit
    form = SettlementRunForm(DummyPostData({
        'start': '2020-02-02',
        'end': '2020-03-03'
    }))
    form.model = SettlementRun()
    form.request = dummy_request
    assert not form.validate()
    assert 'start' not in form.errors
    assert 'end' not in form.errors

    form = SettlementRunForm(DummyPostData({
        'start': '2022-02-02',
        'end': '2022-03-03'
    }))
    form.model = SettlementRun()
    form.request = dummy_request
    assert not form.validate()
    assert form.errors['start'][0].startswith('Dates overlap')
    assert form.errors['end'][0].startswith('Dates overlap')

    form = SettlementRunForm(DummyPostData({
        'start': '2022-02-02',
        'end': '2022-03-03'
    }))
    form.model = settlement_run
    form.request = dummy_request
    assert not form.validate()
    assert 'start' not in form.errors
    assert 'end' not in form.errors
