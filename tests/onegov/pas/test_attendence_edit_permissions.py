import pytest
import transaction

from datetime import date
from decimal import Decimal
from uuid import uuid4
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections.commission import PASCommissionCollection
from onegov.pas.models import (
    Attendence,
    PASCommissionMembership,
    PASParliamentarianRole,
    SettlementRun,
)
from onegov.user import UserCollection

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.shared.client import Client
    from .conftest import TestPasApp


@pytest.mark.parametrize(
    'bulk,state,allowed',
    [
        (False, 'finish_on_save', True),
        (True, 'finish_on_save', True),
        (True, 'closed_after_open', False),
        (False, 'foreign_commission', False),
        (False, 'run_closed', False),
        (False, 'other_closures', True),
        (False, 'tamper_commission', False),
        (True, 'tamper_date', False),
        (False, 'tamper_identity', False),
        (True, 'tamper_identity', False),
    ],
)
def test_commission_president_edit_attendence(
    client: Client[TestPasApp],
    bulk: bool,
    state: str,
    allowed: bool,
) -> None:
    session = client.app.session()
    run = SettlementRun(
        name='2024',
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        active=True,
        closed=False,
    )
    session.add(run)
    session.add(
        SettlementRun(
            name='2023',
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
            active=False,
            closed=True,
        )
    )
    people = PASParliamentarianCollection(client.app)
    president = people.add(
        first_name='Alice',
        last_name='President',
        email_primary='alice@example.org',
        zg_username='zgalice',
    )
    member = people.add(
        first_name='Bob',
        last_name='Member',
        email_primary='bob@example.org',
        zg_username='zgbob',
    )
    commissions = PASCommissionCollection(session)
    own = commissions.add(name='Finanzkommission')
    other = commissions.add(name='Bildungskommission')
    for person in (president, member):
        session.add(
            PASParliamentarianRole(
                parliamentarian_id=person.id,
                role='member',
                meta={'org_type': 'Kantonsrat'},
            )
        )
        for commission in (own, other):
            session.add(
                PASCommissionMembership(
                    parliamentarian_id=person.id,
                    commission_id=commission.id,
                    role=(
                        'president'
                        if person == president and commission == own
                        else 'member'
                    ),
                )
            )
    target_commission = other if state == 'foreign_commission' else own
    group_id = uuid4() if bulk else None
    records: list[Attendence] = []
    for person in ((member, president) if bulk else (member,)):
        record = Attendence(
            parliamentarian=person,
            commission=target_commission,
            date=date(2024, 6, 1),
            duration=Decimal('120'),
            type='commission',
            bulk_edit_id=group_id,
            abschluss=False,
        )
        session.add(record)
        records.append(record)
    if state == 'other_closures':
        for commission, year in ((other, 2024), (own, 2023)):
            session.add(
                Attendence(
                    parliamentarian=president,
                    commission=commission,
                    date=date(year, 7, 1),
                    duration=Decimal('0'),
                    type='commission',
                    abschluss=True,
                )
            )
    user = UserCollection(session).by_username('zgalice')
    assert user is not None
    user.role = 'commission_president'
    user.password = 'test'
    user.active = True
    session.flush()
    count_before = session.query(Attendence).count()
    record_ids = [record.id for record in records]
    run_id = run.id
    other_id = str(other.id)
    president_id = str(president.id)
    endpoint = 'edit-commission-bulk-attendences' if bulk else 'edit'
    url = f'/attendence/{record_ids[0]}/{endpoint}'
    transaction.commit()

    client.login_admin()
    form = client.get(url).form
    form['duration'] = '3'
    if state == 'run_closed':
        session = client.app.session()
        stored_run = session.get(SettlementRun, run_id)
        assert stored_run is not None
        stored_run.closed = True
        transaction.commit()
    client.logout()
    client.login('zgalice', 'test')

    if allowed or state.startswith('tamper_') or state == 'closed_after_open':
        page = client.get(url)
        assert page.status_code == 200
        form = page.form
        form['duration'] = '3'
        detail = client.get(f'/attendence/{record_ids[0]}')
        assert detail.pyquery('a.edit-link')
        assert not detail.pyquery('a.delete-link')
        listing = client.get('/attendences')
        assert record_ids[0].hex in listing.text
    else:
        token_form = client.get('/attendences/new').form
        form['csrf_token'] = token_form['csrf_token'].value
    if state == 'closed_after_open':
        session = client.app.session()
        stored_record = session.get(Attendence, record_ids[0])
        assert stored_record is not None
        stored_record.abschluss = True
        transaction.commit()
    elif state == 'tamper_commission':
        form['commission_id'].force_value(other_id)
    elif state == 'tamper_date':
        form['date'] = '2023-06-01'
    elif state == 'tamper_identity':
        if bulk:
            form['bulk_edit_id'] = str(uuid4())
        else:
            form['parliamentarian_id'] = president_id
    elif state == 'finish_on_save':
        form['abschluss'] = True

    response = form.submit()
    if allowed:
        assert response.status_code == 302, response.pyquery('.error').text()
    response.maybe_follow()
    session = client.app.session()
    assert session.query(Attendence).count() == count_before
    durations = [
        record.duration
        for record in session.query(Attendence).filter(
            Attendence.id.in_(record_ids)
        )
    ]
    assert durations == [Decimal('180' if allowed else '120')] * len(
        record_ids
    )
    if state.startswith('tamper_'):
        return
    page = client.get(url)
    if allowed and state != 'finish_on_save':
        assert page.status_code == 200
        assert page.form['duration'].value == '3.00'
    else:
        assert page.status_code == 302
        assert page.location is not None
        assert page.location.endswith('/attendences')
        detail = client.get(f'/attendence/{record_ids[0]}')
        assert not detail.pyquery('a.edit-link')
