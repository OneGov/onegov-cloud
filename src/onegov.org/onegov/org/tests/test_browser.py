def test_browse_activities(browser, org_app_url):
    browser.baseurl = org_app_url

    # admins
    browser.login_admin()
    browser.visit('/timeline')

    assert browser.is_text_present("Noch keine Aktivität")

    # anonymous
    other = browser.clone()
    other.visit('/timeline')

    assert not other.is_text_present("Noch keine Aktivität")
