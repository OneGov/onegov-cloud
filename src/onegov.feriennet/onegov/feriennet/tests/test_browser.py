import time
import transaction

from datetime import date, datetime, timedelta
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.user import UserCollection
from onegov.core.utils import Bunch


def test_browse_matching(browser, feriennet_app):
    activities = ActivityCollection(feriennet_app.session(), type='vacation')
    attendees = AttendeeCollection(feriennet_app.session())
    bookings = BookingCollection(feriennet_app.session())
    periods = PeriodCollection(feriennet_app.session())
    occasions = OccasionCollection(feriennet_app.session())

    owner = Bunch(username='admin@example.org')

    prebooking = tuple(d.date() for d in (
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1)
    ))

    execution = tuple(d.date() for d in (
        datetime.now() + timedelta(days=10),
        datetime.now() + timedelta(days=12)
    ))

    period = periods.add(
        title="Ferienpass 2016",
        prebooking=prebooking,
        execution=execution,
        active=True
    )

    o = []

    for i in range(2):
        a = activities.add("A {}".format(i), username='admin@example.org')
        a.propose().accept()

        o.append(occasions.add(
            start=datetime(2016, 10, 8 + i, 8),
            end=datetime(2016, 10, 8 + i, 16),
            age=(0, 10),
            spots=(2, 4),
            timezone="Europe/Zurich",
            activity=a,
            period=period
        ))

    a1 = attendees.add(owner, 'Dustin', date(2000, 1, 1), 'female')
    a2 = attendees.add(owner, 'Mike', date(2000, 1, 1), 'female')

    # the first course has enough attendees
    bookings.add(owner, a1, o[0])
    bookings.add(owner, a2, o[0])

    # the second one does not
    bookings.add(owner, a1, o[1])

    transaction.commit()

    browser.login_admin()
    browser.visit('/matching')

    # check the initial state
    assert browser.is_text_present("Ferienpass 2016")
    assert browser.is_text_present("Zufriedenheit liegt bei 0%")
    assert browser.is_text_present("0% aller Durchführungen haben genug")
    assert browser.is_text_present("0 / 4")

    # run a matching
    browser.find_by_value("Zuteilung ausführen").click()

    # check the results
    assert browser.is_text_present("Zufriedenheit liegt bei 100%")
    assert browser.is_text_present("50% aller Durchführungen haben genug")
    assert browser.is_text_present("1 / 4")
    assert browser.is_text_present("2 / 4")

    # try to toggle some details
    assert not browser.is_text_present("Dustin")
    assert not browser.is_text_present("Mike")

    browser.find_by_css('.matching-details > button')[0].click()
    browser.is_element_visible_by_css('.matches')

    assert browser.is_text_present("Dustin")
    assert browser.is_text_present("Mike")

    # reset it again
    browser.find_by_css('.reset-matching').click()

    # without this we sometimes get errors
    time.sleep(0.25)

    # confirm the matching
    assert browser.is_text_present("Zufriedenheit liegt bei 0%")
    assert browser.is_text_present("0% aller Durchführungen haben genug")

    browser.find_by_css('input[value="yes"]').click()
    browser.find_by_css('input[name="sure"]').click()
    browser.find_by_value("Zuteilung ausführen").click()

    assert browser.is_text_present("wurde bereits bestätigt")

    # verify the period's state
    browser.visit('/periods')
    assert browser.is_text_present("Abgeschlossen")


def test_browse_billing(browser, feriennet_app, postgres):

    activities = ActivityCollection(feriennet_app.session(), type='vacation')
    attendees = AttendeeCollection(feriennet_app.session())
    periods = PeriodCollection(feriennet_app.session())
    occasions = OccasionCollection(feriennet_app.session())
    bookings = BookingCollection(feriennet_app.session())

    owner = Bunch(username='admin@example.org')

    prebooking = tuple(d.date() for d in (
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1)
    ))

    execution = tuple(d.date() for d in (
        datetime.now() + timedelta(days=10),
        datetime.now() + timedelta(days=12)
    ))

    period = periods.add(
        title="Ferienpass 2016",
        prebooking=prebooking,
        execution=execution,
        active=True
    )
    period.confirmed = True

    users = UserCollection(feriennet_app.session())
    users.by_username('admin@example.org').realname = 'Jane Doe'

    member = users.add('member@example.org', 'hunter2', 'member')
    member.realname = 'John Doe'

    foobar = activities.add("Foobar", username='admin@example.org')
    foobar.propose().accept()

    o1 = occasions.add(
        start=datetime(2016, 11, 25, 8),
        end=datetime(2016, 11, 25, 16),
        age=(0, 10),
        spots=(0, 2),
        timezone="Europe/Zurich",
        activity=foobar,
        period=period,
        cost=100,
    )

    o2 = occasions.add(
        start=datetime(2016, 11, 25, 17),
        end=datetime(2016, 11, 25, 20),
        age=(0, 10),
        spots=(0, 2),
        timezone="Europe/Zurich",
        activity=foobar,
        period=period,
        cost=1000,
    )

    a1 = attendees.add(owner, 'Dustin', date(2000, 1, 1), 'female')
    a2 = attendees.add(member, 'Mike', date(2000, 1, 1), 'female')

    b1 = bookings.add(owner, a1, o1)
    b2 = bookings.add(owner, a1, o2)
    b3 = bookings.add(member, a2, o1)
    b4 = bookings.add(member, a2, o2)

    b1.state = 'accepted'
    b2.state = 'cancelled'
    b3.state = 'accepted'
    b4.state = 'accepted'

    b1.cost = 100
    b2.cost = 1000
    b3.cost = 100
    b4.cost = 1000

    transaction.commit()

    admin = browser
    member = browser.clone()

    admin.login_admin()
    member.login('member@example.org', 'hunter2')

    # initially there are no bills
    admin.visit('/billing')
    assert admin.is_text_present("noch keine Rechnungen")

    # they can be created
    admin.find_by_css("input[type='submit']").click()
    assert admin.is_text_present("John Doe")
    assert admin.is_text_present("Jane Doe")

    # as long as the period is not finalized, there's no way to pay
    admin.visit('/billing?username=admin@example.org')
    assert admin.is_text_present('100.00 Ausstehend')

    admin.visit('/billing?username=member@example.org')
    assert admin.is_text_present('1100.00 Ausstehend')

    assert 'mark-paid' not in admin.html

    # as long as the period is not finalized, there are no invoices
    for client in (member, admin):
        client.visit('/')
        assert client.find_by_css('.invoices-count').first['data-count'] == '0'

        client.visit('/my-bills')
        assert client.is_text_present("noch keine Rechnungen")

    # once the period is finalized, the invoices become public and they
    # may be marked as paid
    admin.visit('/billing')
    admin.find_by_css('input[value="yes"]').click()
    admin.find_by_css('input[name="sure"]').click()
    admin.find_by_css("input[type='submit']").click()

    for client in (member, admin):
        client.visit('/')
        assert client.find_by_css('.invoices-count').first['data-count'] == '1'

        client.visit('/my-bills')
        assert not client.is_text_present('noch keine Rechnungen')
        assert client.is_text_present("Ferienpass 2016")

    admin.visit('/billing?username=member@example.org')
    assert client.is_text_present('1100.00 Ausstehend')

    # we'll test a few scenarios here
    postgres.save()

    # pay the bill bit by bit
    assert not admin.is_element_present_by_css('.paid')

    admin.find_by_css('.bill button').click()
    admin.find_by_css('table .unpaid .actions-button').first.click()
    admin.find_by_css('table .unpaid .mark-paid').first.click()

    time.sleep(0.25)
    assert admin.is_element_present_by_css('.paid')
    assert admin.is_element_present_by_css('.unpaid')

    admin.find_by_css('table .unpaid .actions-button').first.click()
    admin.find_by_css('table .unpaid .mark-paid').first.click()

    time.sleep(0.25)
    assert admin.is_element_present_by_css('.paid')
    assert not admin.is_element_present_by_css('.unpaid')

    # try to introduce a manual booking
    postgres.undo()

    admin.visit('/billing')
    admin.find_by_css('.dropdown.right-side').click()
    admin.find_by_css('.new-booking').click()

    admin.choose('target', 'all')
    admin.choose('kind', 'discount')
    admin.find_by_css('#booking_text').fill('Rabatt')
    admin.find_by_css('#discount').fill('1.00')
    admin.find_by_value("Absenden").click()

    assert admin.is_text_present("2 manuelle Buchungen wurden erstellt")
    assert admin.is_element_present_by_css('.remove-manual')

    # remove the manual booking
    admin.find_by_css('.dropdown.right-side').click()
    admin.find_by_css('.remove-manual').click()

    assert admin.is_text_present("2 Buchungen entfernen")
    admin.find_by_text("2 Buchungen entfernen").click()

    time.sleep(0.25)
    assert not admin.is_element_present_by_css('.remove-manual')
