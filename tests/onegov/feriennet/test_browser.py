import time
import json
import pytest

from datetime import timedelta
from psycopg2.extras import NumericRange
from pytest import mark
from sedate import as_datetime, replace_timezone


@mark.skip('Login with selenium is not working')
def test_browse_matching(browser, scenario):
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

    # check the initial state
    assert browser.is_text_present("Ferienpass 2016")
    assert browser.is_text_present("Zufriedenheit liegt bei 0%")
    assert browser.is_text_present("0% aller Durchführungen haben genügend")
    assert browser.is_text_present("0 / 4")

    # run a matching
    browser.find_by_value("Zuteilung ausführen").click()

    # check the results
    assert browser.is_text_present("Zufriedenheit liegt bei 100%")
    assert browser.is_text_present("50% aller Durchführungen haben genügend")
    assert browser.is_text_present("1 / 4")
    assert browser.is_text_present("2 / 4")

    # try to toggle some details
    assert not browser.is_text_present("Dustin")
    assert not browser.is_text_present("Mike")

    browser.find_by_css('.matching-details > button')[0].click()
    browser.find_by_css('.matches').is_visible()

    assert browser.is_text_present("Dustin")
    assert browser.is_text_present("Mike")

    # reset it again
    browser.find_by_css('.reset-matching').click()

    # without this we sometimes get errors
    time.sleep(0.25)

    # confirm the matching
    assert browser.is_text_present("Zufriedenheit liegt bei 0%")
    assert browser.is_text_present("0% aller Durchführungen haben genügend")

    browser.find_by_css('input[value="yes"]').click()
    browser.find_by_css('input[name="sure"]').click()
    browser.find_by_value("Zuteilung ausführen").click()

    assert browser.is_text_present("wurde bereits bestätigt")

    # verify the period's state
    browser.visit('/periods')
    assert 'finished prebooking' in browser.html


@mark.skip('Causes too many requests, skip for now')
def test_browse_billing(browser, scenario, postgres):
    scenario.add_period(title="Ferienpass 2016", confirmed=True)
    scenario.add_activity(title="Foobar", state='accepted')
    scenario.add_user(username='member@example.org', role='member')

    scenario.c.users.by_username('admin@example.org').realname = 'Jane Doe'
    scenario.c.users.by_username('member@example.org').realname = 'John Doe'

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


# The parametrization is used to ensure all the volunteer states can
# be reached by clicking in the browser and verify that the states
# can be exported properly
@mark.skip('Causes too many requests, skip for now')
@pytest.mark.parametrize('to_volunteer_state', [
    ('Kontaktiert'),
    ('Bestätigt'),
    ('Offen'),
])
def test_volunteers_export(browser, scenario, to_volunteer_state):
    scenario.add_period(title="Ferienpass 2019", active=True, confirmed=True)
    scenario.add_activity(title="Zoo", state='accepted')
    scenario.add_user(username='member@example.org', role='member')
    scenario.add_occasion(age=(0, 10), spots=(0, 2), cost=100)
    scenario.add_need(
        name="Begleiter", number=NumericRange(1, 4), accept_signups=True)
    scenario.add_attendee(name="Dustin")
    scenario.add_booking(
        username='admin@example.org',
        occasion=scenario.occasions[0],
        state='accepted',
        cost=100
    )
    scenario.commit()
    scenario.refresh()

    # initially, the volunteer feature is disabled
    browser.visit('/')
    assert not browser.is_text_present('Helfen')

    # once activated, it is public
    browser.login_admin()
    browser.visit('/feriennet-settings')
    browser.fill_form({
        'volunteers': 'enabled',
        'tos_url': 'https://example.org/tos'
    })
    browser.find_by_value("Absenden").click()

    browser.visit('/')
    assert browser.is_text_present('Helfen')

    # users can sign up as volunteers
    browser.links.find_by_text("Helfen").click()
    assert browser.is_text_present("Begleiter")
    assert not browser.is_element_present_by_css('.volunteer-cart-item')

    browser.links.find_by_partial_text("Zu meiner Liste").click()
    assert browser.is_element_present_by_css('.volunteer-cart-item')

    browser.links.find_by_text("Als Hilfsperson registrieren").click()
    browser.fill_form({
        'first_name': "Foo",
        'last_name': "Bar",
        'birth_date': '06.04.1984',
        'address': 'Foostreet 1',
        'zip_code': '1234',
        'place': 'Bartown',
        'email': 'foo@bar.org',
        'phone': '1234'
    })
    browser.find_by_value("Absenden").click()

    # the volunteer is not in the helpers list yet
    browser.visit('/attendees/zoo')
    assert not browser.is_text_present("Foo")

    # the admin can see the signed-up users
    browser.visit(f'/volunteers/{scenario.latest_period.id.hex}')
    assert browser.is_text_present("Foo")

    # verify initial volunteer state
    assert browser.is_text_present("Offen")

    browser.find_by_css('.actions-button').first.click()
    # move volunteer through different volunteer states
    if to_volunteer_state == 'Offen':
        pass
    elif to_volunteer_state == 'Kontaktiert':
        assert not browser.is_text_present("Bestätigt")
        browser.links.find_by_partial_text("Als kontaktiert markieren").click()
        assert browser.is_text_present("Kontaktiert")
    elif to_volunteer_state == 'Bestätigt':
        assert not browser.is_text_present("Bestätigt")
        browser.links.find_by_partial_text("Als bestätigt markieren").click()
        assert browser.is_text_present("Bestätigt")
        # now the volunteer is in the list
        browser.visit('/attendees/zoo')
        assert browser.is_text_present("Foo")
    else:
        # invalid case
        raise AssertionError()

    browser.visit('/export/helfer')
    browser.fill_form({
        'period': scenario.periods[0].id.hex,
        'file_format': "json",
    })
    browser.find_by_value("Absenden").click()

    volunteer_export = json.loads(browser.find_by_tag('pre').text)[0]

    occasion_date = as_datetime(scenario.date_offset(10))
    occasion_date = replace_timezone(occasion_date, 'Europe/Zurich')
    start_time = occasion_date.isoformat()
    end_time = (occasion_date + timedelta(hours=1)).isoformat()

    def get_number_of_confirmed_volunteers(state):
        if state == 'Bestätigt':
            return 1
        return 0

    volunteer_json = {
        'Angebot Titel': 'Zoo',
        'Durchführung Daten': [
            [start_time, end_time]
        ],
        'Durchführung Abgesagt': False,
        'Bedarf Name': 'Begleiter',
        'Bedarf Anzahl': '1 - 3',
        'Bestätigte Helfer': get_number_of_confirmed_volunteers(
            to_volunteer_state),
        'Helfer Status': to_volunteer_state,
        'Vorname': 'Foo',
        'Nachname': 'Bar',
        'Geburtsdatum': '1984-06-04',
        'Organisation': '',
        'Ort': 'Bartown',
        'E-Mail': 'foo@bar.org',
        'Telefon': '1234',
        'Adresse': 'Foostreet 1'
    }
    assert volunteer_export == volunteer_json
