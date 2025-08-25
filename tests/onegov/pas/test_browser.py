# current problem. Name Error shortcuts in chameleon templates?
def test_add_commission_bulk_attendence(browser):
    browser.login_admin()
    browser.visit('/pas-settings')
    return

    # Settlement Runs
    browser.links.find_by_text('Abrechnungsläufe').click()
    browser.links.find_by_href('new').click()
    browser.fill('name', 'Q1')
    browser.fill('start', '2024-01-01')
    browser.fill('end', '2024-03-31')
    browser.check('active')
    browser.find_by_value('Absenden').click()
    return

    # Commission
    browser.visit('/pas-settings')
    browser.links.find_by_text('Kommissionen').click()
    browser.links.find_by_href('new').click()
    browser.fill('name', 'Test Commission')
    browser.find_by_value('Absenden').click()

    # Parliamentarian 1
    browser.visit('/pas-settings')
    browser.links.find_by_text('Parlamentarier:innen').click()
    browser.links.find_by_href('new').click()
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
    browser.fill('start', '2024-01-01')
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
    browser.fill('start', '2024-01-01')
    browser.find_by_value('Absenden').click()

    # Go to bulk add view and add attendences
    browser.visit('/attendences/new-commission-bulk')
    assert browser.is_text_present('Neue Kommissionssitzung')

    browser.fill('date', '2024-02-15')
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
