import transaction

from datetime import date, datetime, timedelta
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
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
