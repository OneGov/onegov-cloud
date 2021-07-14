"""
Integration tests using a real browser and taking snapshots along the way.

"""
from time import sleep
from typing import Tuple, Optional

import requests


def has_status(url, code):
    return requests.get(url).status_code == code


def submit_form(
        browser, url,
        snapshot_before=False,
        snapshot_after=False,
        snapshot_name=None,
        form_values: Optional[Tuple[Tuple[str]]] = None
):
    add_suffix = snapshot_before and snapshot_after
    browser.visit(url)

    if form_values:
        browser.fill_form(form_values)

    if snapshot_before:
        if add_suffix:
            snapshot_name = f"{snapshot_name} before submit"
        browser.snapshot(snapshot_name)

    browser.find_by_css('form input[type="submit"]').last.click()

    if snapshot_after:
        if add_suffix:
            snapshot_name = f"{snapshot_name} after submit"
        browser.snapshot(snapshot_name, use_url=True)


def test_new_user_sets_up_all_settings(browser):
    """
    Replaces org tests:
    - test_views_auth.py
        - test_login
    """

    # user goes to logout pages, receives 403
    assert has_status(f'{browser.baseurl}/auth/logout', 403)
    browser.visit('/')
    browser.find_by_text('Anmelden').click()

    assert browser.is_text_present('E-Mail Adresse')
    assert browser.is_text_present('Passwort')
    browser.fill('username', 'admin@example.org')
    browser.fill('password', 'wrong')
    browser.find_by_value("Anmelden").click()

    assert browser.is_text_present(
        'Falsche E-Mail Adresse, falsches Passwort oder falscher Yubikey.')

    browser.fill('password', 'hunter2')
    browser.find_by_value("Anmelden").click()
    assert browser.is_text_present('Sie wurden angemeldet', wait_time=.5)
    browser.percy.snapshot(browser, "Admin logged in to homepage")

    # get all the settings links
    browser.visit('/settings')
    org_settings = browser.find_by_css('.org-settings a')
    org_setting_urls = [a['href'] for a in org_settings]

    for setting_url in org_setting_urls:
        submit_form(
            browser,
            setting_url,
            snapshot_before=True,
            snapshot_after=True,
        )

    # Finally logout
    assert browser.find_by_css('.globals a.logout').first.html == 'Abmelden'
    user_drop = browser.find_by_css('a.dropdown.user').first
    user_drop.mouse_over()
    logout_btn = browser.find_by_text('Abmelden')
    assert logout_btn.visible
    logout_btn.click()
    assert browser.is_text_present('Anmelden', wait_time=.25)
    assert browser.is_text_present('Sie wurden ausgeloggt.')
    browser.snapshot("Admin logged out")
