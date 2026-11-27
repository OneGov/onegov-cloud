from __future__ import annotations

import datetime
import pytest
import re
import transaction

from decimal import Decimal
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.models import Attendence
from onegov.pas.models import PASCommissionMembership
from onegov.pas.models import PASParliamentarianRole
from onegov.pas.models import SettlementRun
from onegov.user import UserCollection
from uuid import uuid4


from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Locator
    from tests.shared.browser import ExtendedBrowser
    from uuid import UUID
    from .conftest import TestPasApp


VALID_DATE = '2024-02-04'
OUTSIDE_RUN_DATE = '2000-01-01'
OUTSIDE_RUN_ERROR = 'Nicht in einem aktiven Abrechungslauf'
INSUFFICIENT = 'Unzureichende Berechtigungen.'


def add_people(
    app: TestPasApp,
    commissions: dict[str, tuple[tuple[str, Any, Any, bool], ...]],
) -> dict[str, UUID]:
    """Adds commissions with members given as (name, start, end,
    kantonsrat). Returns the ids of all parliamentarians and commissions.

    """
    session = app.session()
    people = PASParliamentarianCollection(app)
    ids: dict[str, UUID] = {}
    for commission_name, members in commissions.items():
        commission = PASCommissionCollection(session).add(name=commission_name)
        ids[commission_name] = commission.id
        for name, start, end, kantonsrat in members:
            person = people.add(
                first_name=name,
                last_name='Test',
                email_primary=f'{name.lower()}@example.org',
                zg_username=f'zg{name.lower()}',
            )
            ids[name] = person.id
            if kantonsrat:
                session.add(
                    PASParliamentarianRole(
                        parliamentarian_id=person.id,
                        role='member',
                        start=start,
                        end=end,
                        meta={'org_type': 'Kantonsrat'},
                    )
                )
            session.add(
                PASCommissionMembership(
                    parliamentarian_id=person.id,
                    commission_id=commission.id,
                    role='president' if name == 'A1' else 'member',
                    start=start,
                    end=end,
                )
            )
    session.flush()
    return ids


def add_parliament(app: TestPasApp) -> dict[str, UUID]:
    """Alpha has president A1 and member A2, Beta has member B1.

    '0 Former' sorts first, but its only member X1 has left the Kantonsrat,
    so the bulk forms have to skip it.

    """
    transaction.begin()
    app.session().add(
        SettlementRun(
            name='Q1',
            start=datetime.date(2024, 1, 1),
            end=datetime.date(2024, 3, 31),
            closed=False,
        )
    )
    since = datetime.date(2020, 1, 1)
    ids = add_people(
        app,
        {
            '0 Former': (('X1', since, None, False),),
            'Alpha': (('A1', since, None, True), ('A2', since, None, True)),
            'Beta': (('B1', since, None, True),),
        },
    )
    transaction.commit()
    return ids


def people_of(ids: dict[str, UUID], *names: str) -> dict[str, UUID]:
    return {name: ids[name] for name in names}


def login_as(
    browser: ExtendedBrowser, app: TestPasApp, name: str, role: str
) -> None:
    transaction.begin()
    user = UserCollection(app.session()).by_username(f'zg{name.lower()}')
    assert user is not None
    user.role = role
    user.password = 'hunter2'
    user.active = True
    transaction.commit()
    browser.login(f'zg{name.lower()}', 'hunter2')


def types(browser: ExtendedBrowser) -> set[str]:
    return set(
        browser.page.locator('input[name="type"]').evaluate_all(
            'inputs => inputs.map(input => input.value)'
        )
    )


def checkbox(browser: ExtendedBrowser, parliamentarian_id: UUID) -> Locator:
    return browser.page.locator(
        f'#parliamentarian_id input[value="{parliamentarian_id.hex}"]'
    )


def row(browser: ExtendedBrowser, parliamentarian_id: UUID) -> Locator:
    return browser.page.locator('#parliamentarian_id li').filter(
        has=browser.page.locator(f'input[value="{parliamentarian_id.hex}"]')
    )


def checked(browser: ExtendedBrowser, ids: dict[str, UUID]) -> set[str]:
    return {
        name
        for name, id in ids.items()
        if checkbox(browser, id).count() and checkbox(browser, id).is_checked()
    }


def visible(browser: ExtendedBrowser, ids: dict[str, UUID]) -> set[str]:
    return {
        name
        for name, id in ids.items()
        if row(browser, id).count() and row(browser, id).is_visible()
    }


def forge_checkbox(browser: ExtendedBrowser, id: UUID) -> None:
    browser.page.evaluate(
        '''id => document.querySelector('#parliamentarian_id')
          .insertAdjacentHTML(
            'beforeend',
            `<li><input type="checkbox" name="parliamentarian_id"
                        value="${id}" checked></li>`
        )''',
        id.hex,
    )


def wait_for_initial_sync(browser: ExtendedBrowser) -> None:
    """custom.js fetches the commission members asynchronously and then
    hides everyone not in the preselected commission."""
    browser.page.wait_for_function(
        '() => document.querySelector('
        '\'#parliamentarian_id li[style*="none"]\')'
    )


def visit_and_capture_json_url(browser: ExtendedBrowser, path: str) -> str:
    """Returns the url of the members request sent by custom.js."""
    with browser.page.expect_response(
        lambda response: 'commissions-parliamentarians-json' in response.url
    ) as response_info:
        browser.visit(path)
    assert response_info.value.ok
    return response_info.value.url


def chosen_results(browser: ExtendedBrowser, field: str) -> Locator:
    return browser.page.locator(f'#{field}_chosen .active-result')


def chosen_select(browser: ExtendedBrowser, field: str, text: str) -> None:
    browser.page.locator(f'#{field}_chosen').click()
    chosen_results(browser, field).filter(
        has_text=re.compile(f'^{re.escape(text)}$')
    ).click()


def chosen_options(browser: ExtendedBrowser, field: str) -> set[str]:
    """The options a user can pick in the chosen dropdown."""
    browser.page.locator(f'#{field}_chosen').click()
    options = {
        text.strip()
        for text in chosen_results(browser, field).all_inner_texts()
    }
    browser.page.keyboard.press('Escape')
    return options


def chosen_value(browser: ExtendedBrowser, field: str) -> str:
    return browser.page.locator(f'#{field}_chosen .chosen-single').inner_text()


def select_commission(browser: ExtendedBrowser, name: str) -> None:
    chosen_select(browser, 'commission_id', name)


def submit(browser: ExtendedBrowser, date: str) -> None:
    browser.fill('date', date)
    browser.fill('duration', '2')
    with browser.page.expect_response(
        lambda response: response.request.method == 'POST'
    ):
        browser.page.locator('button.save-link').click()
    browser.page.wait_for_load_state('networkidle')


def open_bulk_edit(browser: ExtendedBrowser, app: TestPasApp) -> None:
    transaction.begin()
    (attendence_id,) = app.session().query(Attendence.id).first()  # type: ignore[misc]
    transaction.abort()
    browser.visit(f'/attendence/{attendence_id.hex}')
    browser.page.locator('a.edit-link').click()
    browser.page.wait_for_load_state('networkidle')
    assert 'bulk-attendences' in browser.url


def snapshot(app: TestPasApp) -> set[tuple[Any, ...]]:
    transaction.begin()
    result = {
        (
            a.parliamentarian_id,
            a.commission_id,
            a.type,
            a.date,
            a.duration,
            a.bulk_edit_id,
        )
        for a in app.session().query(Attendence)
    }
    transaction.abort()
    return result


def booked(app: TestPasApp, ids: dict[str, UUID]) -> set[str]:
    booked_ids = {entry[0] for entry in snapshot(app)}
    return {name for name, id in ids.items() if id in booked_ids}


def stored(
    app: TestPasApp, ids: dict[str, UUID]
) -> dict[str, tuple[Any, ...]]:
    names = {id: name for name, id in ids.items()}
    return {
        names[parliamentarian_id]: (type, commission_id, duration)
        for parliamentarian_id, commission_id, type, _, duration, _ in (
            snapshot(app)
        )
    }


def bulk_edit_ids(app: TestPasApp) -> set[UUID | None]:
    return {entry[5] for entry in snapshot(app)}


def test_plenary_bulk_add_and_edit(browser: ExtendedBrowser) -> None:
    app: TestPasApp = browser.wsgi_server.app  # type: ignore[attr-defined]
    people = people_of(add_parliament(app), 'A1', 'A2', 'B1', 'X1')
    counter = browser.page.locator('#parliamentarian_id li strong')

    browser.login_admin()
    browser.visit('/attendences/new-bulk')
    assert checkbox(browser, people['X1']).count() == 0
    assert checked(browser, people) == {'A1', 'A2', 'B1'}
    assert counter.inner_text() == '3 / 3'

    checkbox(browser, people['A2']).uncheck()
    assert counter.inner_text() == '2 / 3'

    # the selection survives a failed submit
    submit(browser, OUTSIDE_RUN_DATE)
    assert browser.is_text_present(OUTSIDE_RUN_ERROR)
    assert checked(browser, people) == {'A1', 'B1'}
    assert counter.inner_text() == '2 / 3'

    submit(browser, VALID_DATE)
    assert browser.is_text_present('Plenarsitzung hinzugefügt')
    assert booked(app, people) == {'A1', 'B1'}

    open_bulk_edit(browser, app)
    assert checked(browser, people) == {'A1', 'B1'}
    checkbox(browser, people['A2']).check()
    checkbox(browser, people['B1']).uncheck()

    submit(browser, OUTSIDE_RUN_DATE)
    assert browser.is_text_present(OUTSIDE_RUN_ERROR)
    assert checked(browser, people) == {'A1', 'A2'}

    submit(browser, VALID_DATE)
    assert browser.is_text_present('Anwesenheiten bearbeitet')
    assert booked(app, people) == {'A1', 'A2'}
    assert len(bulk_edit_ids(app)) == 1


@pytest.mark.parametrize(
    'path,meeting_type',
    [
        ('/attendences/new-commission-bulk', 'shortest'),
        ('/attendences/new-file-study-bulk', 'study'),
    ],
)
def test_commission_bulk_add_syncs_parliamentarians_with_commission(
    browser: ExtendedBrowser, path: str, meeting_type: str
) -> None:
    app: TestPasApp = browser.wsgi_server.app  # type: ignore[attr-defined]
    ids = add_parliament(app)
    people = people_of(ids, 'A1', 'A2', 'B1', 'X1')
    # only commission meetings start with all members checked
    preselect = meeting_type != 'study'

    def expected(*names: str) -> set[str]:
        return set(names) if preselect else set()

    browser.login_admin()
    browser.visit(path)
    wait_for_initial_sync(browser)

    # '0 Former' has no active members, so Alpha is selected instead
    assert chosen_options(browser, 'commission_id') == {'Alpha', 'Beta'}
    assert chosen_value(browser, 'commission_id') == 'Alpha'
    assert checkbox(browser, people['X1']).count() == 0
    assert visible(browser, people) == {'A1', 'A2'}
    assert checked(browser, people) == expected('A1', 'A2')

    # switching resets the selection to the new commission's members
    select_commission(browser, 'Beta')
    assert visible(browser, people) == {'B1'}
    assert checked(browser, people) == expected('B1')
    checkbox(browser, people['B1']).check()
    select_commission(browser, 'Alpha')
    assert visible(browser, people) == {'A1', 'A2'}
    assert checked(browser, people) == expected('A1', 'A2')

    checkbox(browser, people['A1']).check()
    checkbox(browser, people['A2']).uncheck()
    if preselect:
        browser.choose('type', meeting_type)
    else:
        assert not types(browser)

    # the selection survives a failed submit
    submit(browser, OUTSIDE_RUN_DATE)
    assert browser.is_text_present(OUTSIDE_RUN_ERROR)
    wait_for_initial_sync(browser)
    assert visible(browser, people) == {'A1', 'A2'}
    assert checked(browser, people) == {'A1'}

    submit(browser, VALID_DATE)
    assert browser.is_text_present('Sitzung hinzugefügt')
    assert stored(app, people) == {
        'A1': (meeting_type, ids['Alpha'], Decimal('120')),
    }


def test_single_add_syncs_commission_and_parliamentarian(
    browser: ExtendedBrowser,
) -> None:
    app: TestPasApp = browser.wsgi_server.app  # type: ignore[attr-defined]
    ids = add_parliament(app)
    people = people_of(ids, 'A1', 'A2', 'B1')
    everyone = {'Test A1', 'Test A2', 'Test B1'}
    commissions = {'-', '0 Former', 'Alpha', 'Beta'}
    commission = browser.page.locator('#commission_id_chosen')

    browser.login_admin()
    browser.visit('/attendences/new')
    browser.page.wait_for_load_state('networkidle')

    # plenary sessions have no commission
    assert (
        browser.page.locator('input[name="type"]:checked').get_attribute(
            'value'
        )
        == 'plenary'
    )
    assert not commission.is_visible()
    browser.choose('type', 'commission')
    assert commission.is_visible()

    assert chosen_options(browser, 'parliamentarian_id') == everyone
    assert chosen_options(browser, 'commission_id') == commissions

    # switching commissions directly drops a parliamentarian who isn't in
    # the new one
    assert chosen_value(browser, 'parliamentarian_id') == 'Test A1'
    chosen_select(browser, 'commission_id', 'Alpha')
    assert chosen_options(browser, 'parliamentarian_id') == {
        'Test A1',
        'Test A2',
    }
    assert chosen_value(browser, 'parliamentarian_id') == 'Test A1'
    chosen_select(browser, 'commission_id', 'Beta')
    assert chosen_options(browser, 'parliamentarian_id') == {'Test B1'}
    assert chosen_value(browser, 'parliamentarian_id') == 'Test B1'
    chosen_select(browser, 'commission_id', '-')

    # a parliamentarian narrows down the commissions
    chosen_select(browser, 'parliamentarian_id', 'Test A2')
    assert chosen_options(browser, 'commission_id') == {'-', 'Alpha'}

    # a commission narrows down the parliamentarians
    chosen_select(browser, 'commission_id', 'Alpha')
    assert chosen_options(browser, 'parliamentarian_id') == {
        'Test A1',
        'Test A2',
    }
    assert chosen_value(browser, 'parliamentarian_id') == 'Test A2'

    # going back to '-' lifts the restriction, so someone from another
    # commission can be picked, which in turn narrows the commissions
    chosen_select(browser, 'commission_id', '-')
    assert chosen_options(browser, 'parliamentarian_id') == everyone
    chosen_select(browser, 'parliamentarian_id', 'Test B1')
    assert chosen_options(browser, 'commission_id') == {'-', 'Beta'}
    chosen_select(browser, 'commission_id', 'Beta')

    submit(browser, VALID_DATE)
    assert browser.is_text_present('Neue Anwesenheit hinzugefügt')
    assert stored(app, people) == {
        'B1': ('commission', ids['Beta'], Decimal('120')),
    }


def test_commission_president_adds_and_edits_attendences(
    browser: ExtendedBrowser,
) -> None:
    app: TestPasApp = browser.wsgi_server.app  # type: ignore[attr-defined]
    ids = add_parliament(app)
    people = people_of(ids, 'A1', 'A2', 'B1')
    login_as(browser, app, 'A1', 'commission_president')

    # single: themselves and the members of the commission they lead
    browser.visit('/attendences/new')
    browser.page.wait_for_load_state('networkidle')
    assert 'plenary' not in types(browser)
    browser.choose('type', 'commission')
    assert chosen_options(browser, 'parliamentarian_id') == {
        'Test A1',
        'Test A2',
    }
    assert chosen_options(browser, 'commission_id') == {'-', 'Alpha'}

    # bulk: only the commission they lead, other people aren't rendered
    browser.visit('/attendences/new-commission-bulk')
    browser.page.wait_for_load_state('networkidle')
    assert chosen_options(browser, 'commission_id') == {'Alpha'}
    assert checkbox(browser, people['B1']).count() == 0
    assert visible(browser, people) == {'A1', 'A2'}
    assert checked(browser, people) == {'A1', 'A2'}

    # a forged checkbox for someone outside their commission is rejected,
    # the legitimate part of the selection is kept
    checkbox(browser, people['A2']).uncheck()
    forge_checkbox(browser, people['B1'])
    submit(browser, VALID_DATE)
    assert browser.is_text_present(
        f"'{people['B1']}' is not a valid choice for this field."
    )
    assert booked(app, people) == set()
    assert checkbox(browser, people['B1']).count() == 0
    assert checked(browser, people) == {'A1'}
    submit(browser, VALID_DATE)
    assert browser.is_text_present('Sitzung hinzugefügt')
    assert booked(app, people) == {'A1'}

    # bulk edit: only the commission's members are offered
    open_bulk_edit(browser, app)
    assert checkbox(browser, people['B1']).count() == 0
    assert visible(browser, people) == {'A1', 'A2'}
    assert checked(browser, people) == {'A1'}
    checkbox(browser, people['A2']).check()
    submit(browser, VALID_DATE)
    assert browser.is_text_present('Anwesenheiten bearbeitet')
    assert booked(app, people) == {'A1', 'A2'}
    before = snapshot(app)

    # the commission is only readonly client-side
    open_bulk_edit(browser, app)
    browser.page.evaluate(
        '''id => {
            const select = document.querySelector('#commission_id');
            select.insertAdjacentHTML(
                'beforeend', `<option value="${id}">Beta</option>`
            );
            select.value = id;
        }''',
        ids['Beta'].hex,
    )
    submit(browser, VALID_DATE)
    assert browser.is_text_present(INSUFFICIENT)
    assert snapshot(app) == before

    open_bulk_edit(browser, app)
    forge_checkbox(browser, people['B1'])
    submit(browser, VALID_DATE)
    assert browser.is_text_present(INSUFFICIENT)
    assert snapshot(app) == before

    # the selection survives a failed submit
    open_bulk_edit(browser, app)
    checkbox(browser, people['A1']).uncheck()
    submit(browser, OUTSIDE_RUN_DATE)
    assert browser.is_text_present(OUTSIDE_RUN_ERROR)
    assert checked(browser, people) == {'A2'}

    submit(browser, VALID_DATE)
    assert browser.is_text_present('Anwesenheiten bearbeitet')
    assert stored(app, people) == {
        'A2': ('commission', ids['Alpha'], Decimal('120')),
    }
    assert len(bulk_edit_ids(app)) == 1


def test_parliamentarian_adds_own_attendence_only(
    browser: ExtendedBrowser,
) -> None:
    app: TestPasApp = browser.wsgi_server.app  # type: ignore[attr-defined]
    ids = add_parliament(app)
    people = people_of(ids, 'A1', 'A2', 'B1')

    transaction.begin()
    bulk_edit_id = uuid4()
    plenary = {
        name: Attendence(
            parliamentarian_id=people[name],
            date=datetime.date(2024, 2, 1),
            duration=120,
            type='plenary',
            bulk_edit_id=bulk_edit_id,
        )
        for name in ('A1', 'B1')
    }
    app.session().add_all(plenary.values())
    app.session().flush()
    own, other = plenary['B1'].id, plenary['A1'].id
    transaction.commit()
    before = snapshot(app)

    login_as(browser, app, 'B1', 'parliamentarian')

    browser.visit('/attendences/new-bulk')
    assert browser.is_text_present(
        'Sie haben keine Berechtigung, Plenarsitzungen hinzuzufügen.'
    )
    for path in ('new-commission-bulk', 'new-file-study-bulk'):
        browser.visit(f'/attendences/{path}')
        assert browser.is_text_present(
            'Nur Administratoren können Massenanwesenheiten erfassen.'
        )

    # someone else's plenary is forbidden outright, their own is refused
    response = browser.page.goto(
        f'{browser.baseurl}/attendence/{other.hex}'
        '/edit-plenary-bulk-attendences'
    )
    assert response is not None and response.status == 403
    browser.visit(f'/attendence/{own.hex}/edit-plenary-bulk-attendences')
    assert browser.is_text_present(
        'Sie haben keine Berechtigung, Plenarsitzungen zu bearbeiten.'
    )
    assert browser.page.locator('button.save-link').count() == 0
    assert snapshot(app) == before

    browser.visit('/attendences/new')
    browser.page.wait_for_load_state('networkidle')
    assert 'plenary' not in types(browser)
    browser.choose('type', 'commission')
    assert chosen_options(browser, 'parliamentarian_id') == {'Test B1'}
    assert chosen_options(browser, 'commission_id') == {'-', 'Beta'}

    chosen_select(browser, 'commission_id', 'Beta')
    submit(browser, VALID_DATE)
    assert browser.is_text_present('Neue Anwesenheit hinzugefügt')
    assert snapshot(app) - before == {
        (
            people['B1'],
            ids['Beta'],
            'commission',
            datetime.date(2024, 2, 4),
            Decimal('120'),
            None,
        )
    }


def test_settlement_run_selects_parliamentarians(
    browser: ExtendedBrowser,
) -> None:
    app: TestPasApp = browser.wsgi_server.app  # type: ignore[attr-defined]
    transaction.begin()
    session = app.session()
    earlier = SettlementRun(
        name='Q3',
        start=datetime.date(2024, 7, 1),
        end=datetime.date(2024, 9, 30),
        closed=False,
    )
    # the active run, used without settlement_run_id
    session.add(
        SettlementRun(
            name='Q4',
            start=datetime.date(2024, 10, 1),
            end=datetime.date(2024, 12, 31),
            closed=False,
        )
    )
    session.add(earlier)
    date = datetime.date
    ids = add_people(
        app,
        {
            'Gesundheit': (
                ('Anna', date(2024, 1, 1), date(2024, 9, 23), True),
                ('Joined', date(2024, 8, 1), None, True),
                ('Left', date(2024, 1, 1), date(2024, 6, 30), True),
                ('Future', date(2024, 10, 1), None, True),
            ),
            'Finanzen': (('Other', date(2020, 1, 1), None, True),),
        },
    )
    query = f'?settlement_run_id={earlier.id}'
    transaction.commit()
    people = people_of(ids, 'Anna', 'Joined', 'Left', 'Future', 'Other')

    browser.login_admin()
    json_url = visit_and_capture_json_url(
        browser, '/attendences/new-commission-bulk' + query
    )
    assert query[1:] in json_url
    wait_for_initial_sync(browser)
    assert browser.page.locator('input[name="date"]').input_value() == (
        '2024-07-01'
    )
    select_commission(browser, 'Gesundheit')
    assert visible(browser, people) == {'Anna', 'Joined'}
    assert checked(browser, people) == {'Anna', 'Joined'}
    select_commission(browser, 'Finanzen')
    assert visible(browser, people) == {'Other'}
    select_commission(browser, 'Gesundheit')
    submit(browser, '2024-09-01')
    assert browser.is_text_present('Sitzung hinzugefügt')
    assert booked(app, people) == {'Anna', 'Joined'}

    json_url = visit_and_capture_json_url(browser, '/attendences/new' + query)
    assert query[1:] in json_url
    browser.page.wait_for_load_state('networkidle')
    browser.choose('type', 'commission')
    assert chosen_options(browser, 'parliamentarian_id') == {
        'Test Anna',
        'Test Joined',
        'Test Other',
    }
    chosen_select(browser, 'commission_id', 'Gesundheit')
    assert chosen_options(browser, 'parliamentarian_id') == {
        'Test Anna',
        'Test Joined',
    }
