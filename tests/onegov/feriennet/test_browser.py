import time


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
