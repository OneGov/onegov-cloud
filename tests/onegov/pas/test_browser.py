import pytest
from datetime import date

from tests.shared.browser import ExtendedBrowser


@pytest.mark.xdist_group(name="browser")
def test_add_commission_bulk_attendence(browser: ExtendedBrowser):
    browser.login_admin()
    browser.visit('/settlement-runs/new')
    browser.is_element_present_by_name('name', wait_time=10)
    browser.fill('name', 'Q1')
    browser.set_datetime_element('#start', date(2024, month=1, day=1))
    browser.set_datetime_element('#end', date(2024, month=3, day=31))
    browser.check('active')
    browser.find_by_value('Absenden').click()

    # Commission
    browser.visit('/commissions/new')
    browser.fill('name', 'Test Commission')
    browser.find_by_value('Absenden').click()
    return

    # Parliamentarian 1
    browser.visit('/parliamentarians/new')
    browser.select('gender', 'male')
    browser.fill('first_name', 'Peter')
    browser.fill('last_name', 'Muster')
    browser.select('shipping_method', 'a')
    browser.fill('shipping_address', 'Address')
    browser.fill('shipping_address_zip_code', 'ZIP')
    browser.fill('shipping_address_city', 'City')
    browser.fill('email_primary', 'peter.muster@example.org')
    browser.find_by_value('Absenden').click()

    browser.links.find_by_href('new').click()
    browser.select('role', 'member')
    browser.set_datetime_element('start', date(2024, 1, 1))
    browser.find_by_value('Absenden').click()

    # Parliamentarian 2
    browser.visit('/pas-settings')
    browser.links.find_by_text('Parlamentarier:innen').click()
    browser.links.find_by_href('new').click()
    browser.select('gender', 'female')
    browser.fill('first_name', 'Petra')
    browser.fill('last_name', 'Muster')
    browser.select('shipping_method', 'a')
    browser.fill('shipping_address', 'Address')
    browser.fill('shipping_address_zip_code', 'ZIP')
    browser.fill('shipping_address_city', 'City')
    browser.fill('email_primary', 'petra.muster@example.org')
    browser.find_by_value('Absenden').click()

    browser.links.find_by_href('new').click()
    browser.select('role', 'member')
    browser.set_datetime_element('start', date(2024, 1, 1))
    browser.find_by_value('Absenden').click()

    # Go to bulk add view and add attendences
    browser.visit('/attendences/new-commission-bulk')
    assert browser.is_text_present('Neue Kommissionssitzung')

    browser.set_datetime_element('date', date(2024, 2, 15))
    browser.fill('duration', '2.5')
    commission_option = browser.find_option_by_text('Test Commission')
    browser.select('commission_id', commission_option.value)
    peter_option = browser.find_option_by_text('Peter Muster')
    petra_option = browser.find_option_by_text('Petra Muster')
    browser.select('parliamentarian_id', peter_option.value)
    browser.select('parliamentarian_id', petra_option.value)
    browser.find_by_value('Absenden').click()

    assert browser.is_text_present('Kommissionssitzung hinzugefügt')
    browser.visit('/attendences')
    assert browser.is_text_present('15.02.2024')
    assert browser.is_text_present('Peter Muster')
    assert browser.is_text_present('Petra Muster')
    assert browser.is_text_present('Test Commission')
    assert browser.html.count('15.02.2024') == 2
    assert browser.html.count('2.50h') == 2
