from __future__ import annotations

import time
import json
import pytest

from datetime import date, datetime
from pathlib import Path
from datetime import timedelta
from onegov.activity.types import BoundedIntegerRange
from pytest import mark


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared import ExtendedBrowser
    from tests.shared.postgresql import Postgresql
    from .conftest import Scenario
    from .conftest import Client, TestApp


def test_browse_matching(
    browser: ExtendedBrowser,
    scenario: Scenario
) -> None:

    scenario.add_period(title="Ferienpass 2016")

    for i in range(2):
        scenario.add_activity(title=f"A {i}", state='accepted')
        scenario.add_occasion(age=(0, 10), spots=(2, 4))

    dustin = scenario.add_attendee(name="Dustin")
    mike = scenario.add_attendee(name="Mike")

    # the first course has enough attendees
    scenario.add_booking(attendee=dustin, occasion=scenario.occasions[0])
    scenario.add_booking(attendee=mike, occasion=scenario.occasions[0])

    # the second one does not
    scenario.add_booking(attendee=mike, occasion=scenario.occasions[1])

    scenario.commit()

    browser.login_admin()
    browser.visit('/matching')

    # close CMP dialog if it pops up
    try:
        browser.find_by_text("Akzeptieren und schliessen").click()
    except Exception:
        pass

    # check the initial state
    assert browser.is_text_present("Ferienpass 2016")
    assert browser.is_text_present("Zufriedenheit liegt bei 0%")
    assert browser.is_text_present("0% aller Durchführungen haben genügend")
    assert browser.is_text_present("0 / 4")

    # NOTE: There is an uniteractable copy of a lot of the elements on this
    #       page, that we have to avoid trying to interact with, unfortunately
    #       it's located before the interactable version in the DOM.
    #       So we manually target the main content section first and then
    #       target everything relative to that.
    content = browser.find_by_id('content').first

    # run a matching
    content.find_by_value("Zuteilung ausführen").click()

    # check the results
    assert browser.is_text_present("Zufriedenheit liegt bei 100%")
    assert browser.is_text_present("50% aller Durchführungen haben genügend")
    assert browser.is_text_present("1 / 4")
    assert browser.is_text_present("2 / 4")

    # try to toggle some details
    assert not browser.is_text_present("Dustin")
    assert not browser.is_text_present("Mike")

    content.find_by_css('.matching-details .title-toggler')[0].click()
    content.find_by_css('.matches').is_visible()

    assert browser.is_text_present("Dustin")
    assert browser.is_text_present("Mike")

    # reset it again
    content.find_by_css('.reset-matching').click()

    # confirm the matching
    assert browser.is_text_present("Zufriedenheit liegt bei 0%")
    assert browser.is_text_present("0% aller Durchführungen haben genügend")

    content.find_by_css('input[value="yes"]').click()
    content.find_by_css('input[name="sure"]').click()
    content.find_by_value("Zuteilung ausführen").click()

    # verify the period's state
    browser.visit('/periods')
    assert 'finished prebooking' in browser.html


@mark.skip('Causes too many requests, skip for now')
def test_browse_billing(
    browser: ExtendedBrowser,
    scenario: Scenario,
    postgres: Postgresql
) -> None:

    scenario.add_period(title="Ferienpass 2016", confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_user(username='member@example.org', role='member')

    scenario.c.users.by_username('admin@example.org').realname = 'Jane Doe'  # type: ignore[union-attr]
    scenario.c.users.by_username('member@example.org').realname = 'John Doe'  # type: ignore[union-attr]

    scenario.add_occasion(age=(0, 10), spots=(0, 2), cost=100)
    scenario.add_occasion(age=(0, 10), spots=(0, 2), cost=1000)

    scenario.add_attendee(name="Dustin")
    scenario.add_booking(
        username='admin@example.org',
        occasion=scenario.occasions[0],
        state='accepted',
        cost=100
    )
    scenario.add_booking(
        username='admin@example.org',
        occasion=scenario.occasions[1],
        state='cancelled',
        cost=1000
    )

    scenario.add_attendee(name="Mike")
    scenario.add_booking(
        username='member@example.org',
        occasion=scenario.occasions[0],
        state='accepted',
        cost=100
    )
    scenario.add_booking(
        username='member@example.org',
        occasion=scenario.occasions[1],
        state='accepted',
        cost=1000
    )

    scenario.commit()

    browser.login_admin()

    # initially there are no bills
    browser.visit('/billing')
    assert browser.is_text_present("Keine Rechnungen gefunden")

    # they can be created
    browser.find_by_css("input[type='submit']").click()
    assert browser.is_text_present("John Doe")
    assert browser.is_text_present("Jane Doe")

    # as long as the period is not finalized, there's no way to pay
    browser.visit('/billing?username=admin@example.org')
    assert browser.is_text_present('100.00 Ausstehend')

    browser.visit('/billing?username=member@example.org')
    assert browser.is_text_present('1100.00 Ausstehend')

    assert 'mark-paid' not in browser.html

    # as long as the period is not finalized, there are no invoices
    browser.logout()
    browser.login('member@example.org', 'hunter2')

    browser.visit('/')
    assert browser.find_by_css('.invoices-count').first['data-count'] == '0'

    browser.visit('/my-bills')
    assert browser.is_text_present("noch keine Rechnungen")

    browser.logout()
    browser.login_admin()

    browser.visit('/')
    assert browser.find_by_css('.invoices-count').first['data-count'] == '0'

    browser.visit('/my-bills')
    assert browser.is_text_present("noch keine Rechnungen")

    # once the period is finalized, the invoices become public and they
    # may be marked as paid
    browser.visit('/billing')
    browser.find_by_css('input[value="yes"]').click()
    browser.find_by_css('input[name="sure"]').click()
    browser.find_by_css("input[type='submit']").click()

    browser.logout()
    browser.login('member@example.org', 'hunter2')

    browser.visit('/')
    assert browser.find_by_css('.invoices-count').first['data-count'] == '1'

    browser.visit('/my-bills')
    assert not browser.is_text_present('noch keine Rechnungen')
    assert browser.is_text_present("Ferienpass 2016")

    browser.logout()
    browser.login_admin()

    browser.visit('/')
    assert browser.find_by_css('.invoices-count').first['data-count'] == '1'

    browser.visit('/my-bills')
    assert not browser.is_text_present('noch keine Rechnungen')
    assert browser.is_text_present("Ferienpass 2016")

    browser.visit('/billing?username=member@example.org&state=all')
    assert browser.is_text_present('1100.00 Ausstehend')

    # we'll test a few scenarios here
    postgres.save()

    # pay the bill bit by bit
    assert not browser.is_element_present_by_css('.paid')

    browser.find_by_css('.bill button').click()
    browser.find_by_css('table .unpaid .actions-button').first.click()
    browser.find_by_css('table .unpaid .mark-paid').first.click()

    time.sleep(0.25)
    assert browser.is_element_present_by_css('.paid')
    assert browser.is_element_present_by_css('.unpaid')

    browser.find_by_css('table .unpaid .actions-button').first.click()
    browser.find_by_css('table .unpaid .mark-paid').first.click()

    time.sleep(0.25)
    assert browser.is_element_present_by_css('.paid')
    assert not browser.is_element_present_by_css('.unpaid')

    # try to introduce a manual booking
    postgres.undo()

    browser.visit('/billing?state=all')
    browser.find_by_css('.dropdown.right-side').click()
    browser.find_by_css('.new-booking').click()

    browser.choose('target', 'all')
    browser.choose('kind', 'discount')
    browser.find_by_css('#booking_text').fill('Rabatt')
    browser.find_by_css('#discount').fill('1.00')
    browser.find_by_value("Absenden").click()

    assert browser.is_text_present("2 manuelle Buchungen wurden erstellt")
    assert browser.is_element_present_by_css('.remove-manual')

    # remove the manual booking
    browser.find_by_css('.dropdown.right-side').click()
    browser.find_by_css('.remove-manual').click()

    assert browser.is_text_present("2 Buchungen entfernen")
    browser.find_by_text("2 Buchungen entfernen").click()

    time.sleep(0.25)
    assert not browser.is_element_present_by_css('.remove-manual')


# A volunteer can hold any of these states; the 'helfer' export must render
# each label. A missing 'cancelled' label previously raised KeyError (OGC-5YR).
@pytest.mark.parametrize('state,label', [
    ('open', 'Offen'),
    ('contacted', 'Kontaktiert'),
    ('confirmed', 'Bestätigt'),
    ('cancelled', 'Abgelehnt'),
])
def test_volunteers_export(
    browser: ExtendedBrowser,
    scenario: Scenario,
    state: str,
    label: str
) -> None:

    scenario.add_period(title="Ferienpass 2019", active=True, confirmed=True)
    scenario.add_activity(title="Zoo", state='accepted')
    scenario.add_occasion(age=(0, 10), spots=(0, 2), cost=100)
    scenario.add_need(
        name="Begleiter",
        number=BoundedIntegerRange(1, 4),
        accept_signups=True
    )
    scenario.add_volunteer(
        state=state,
        first_name="Foo",
        last_name="Bar",
        birth_date=date(1984, 6, 4),
        organisation="",
        address="Foostreet 1",
        zip_code="1234",
        place="Bartown",
        email="foo@bar.org",
        phone="1234"
    )
    scenario.commit()
    scenario.refresh()

    page = browser.page
    browser.login_admin()

    # the 'helfer' export is admin-only and independent of the feature flag
    browser.visit('/export/helfer')
    page.locator('select[name="period"]').select_option(
        scenario.periods[0].id.hex)
    # the radio input is visually hidden, so check it with force
    page.locator('input[name="file_format"][value="json"]').check(force=True)

    # the json export is served as a file download
    with page.expect_download() as download_info:
        page.locator('input[value="Absenden"]').click()
    export_path = download_info.value.path()

    volunteer = json.loads(Path(export_path).read_text())[0]
    assert volunteer['Angebot Titel'] == 'Zoo'
    assert volunteer['Vorname'] == 'Foo'
    assert volunteer['Helfer Status'] == label
    assert volunteer['Bestätigte Helfer'] == (1 if state == 'confirmed' else 0)


def test_volunteer_subscription(
    browser: ExtendedBrowser,
    scenario: Scenario,
    client: Client[TestApp]
) -> None:

    scenario.add_period(title="2026", confirmed=True, finalized=False)
    scenario.add_activity(title="Photography", state='accepted')

    now = datetime.now()
    later = scenario.date_offset(10)

    later = datetime.combine(later, now.time())
    scenario.add_occasion(
        cost=100, dates=[(later, later + timedelta(hours=1))])
    scenario.add_need(
        name="Aufichtsperson", number=BoundedIntegerRange(1, 3),
        accept_signups=True)

    scenario.add_activity(title="Dancing", state='accepted')
    scenario.add_occasion(cost=100)
    scenario.add_need(
        name="Begleitung", number=BoundedIntegerRange(3, 4),
        accept_signups=True)

    scenario.commit()

    browser.login_admin()
    browser.visit('/feriennet-settings')
    browser.find_by_css('#volunteers-2').click()
    browser.find_by_text("Speichern").click()

    browser.logout()

    browser.visit('/activities/volunteer')
    browser.find_by_text("Photography")
    browser.find_by_text("Dancing")
    browser.find_by_text("Zu meiner Liste")[0].click()
    browser.find_by_text("Zu meiner Liste")[1].click()

    browser.find_by_css(".volunteer-cart .button").click()
    browser.find_by_css("#my-list .button.success").click()
    browser.fill_form({
        'first_name': "Foo",
        'last_name': "Bar",
        'birth_date': '1984-04-06',
        'address': 'Foostreet 1',
        'zip_code': '1234',
        'place': 'Bartown',
        'email': 'foo@bar.org',
        'phone': '1234'
    })
    browser.find_by_value("Absenden").click()

    maildir = Path(client.app.maildir)
    mails = sorted(maildir.iterdir(), key=lambda f: f.stat().st_mtime)
    mail = mails[0]
    with open(mail, 'r') as file:
        mail_content = file.read()
        assert (
            "Sie haben sich als Hilfsperson"
            in mail_content
        )
        assert ("Photography" in mail_content)
        assert ("Dancing" in mail_content)

    browser.login_admin()
    browser.visit('/tickets/ALL/open')
    browser.find_by_css('.ticket-number-plain a').click()
    browser.find_by_text('Ticket annehmen').click()

    assert browser.is_text_present("Photography")
    assert browser.is_text_present("Dancing")
    browser.find_by_text("Als kontaktiert markieren")[0].click()
    assert browser.is_element_present_by_css(".bg-color.contacted")
    browser.find_by_text("Als bestätigt markieren")[0].click()

    browser.find_by_text("Statusmail").click()
    browser.find_by_text("Senden").click()
    assert browser.is_text_present(
        "Nicht alle Anmeldungen befinden sich in einem finalen Zustand.")

    browser.find_by_text("Als abgelehnt markieren")[1].click()

    browser.find_by_text("Statusmail").click()
    browser.find_by_text("Senden").click()
    assert browser.is_text_present(
        "1 E-Mails erfolgreich gesendet")

    mails = sorted(maildir.iterdir(), key=lambda f: f.stat().st_mtime)
    mail = mails[1]
    with open(mail, 'r') as file:
        mail_content = file.read()
        assert (
            "dies ist die finale Liste"
            in mail_content
        )
        assert ("Photography" in mail_content)
        assert ("Dancing" in mail_content)
        assert ("Kein Helferbedarf" in mail_content)
        assert ("Best\\u00e4tigt" in mail_content)
