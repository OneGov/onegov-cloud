"""
Integration tests using a real browser and taking snapshots along the way.

"""
from time import sleep

import requests


def has_status(url, code):
    return requests.get(url).status_code == code


def test_new_user_sets_up_all_settings(browser, percy):
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
    assert browser.is_text_present('Sie wurden angemeldet', wait_time=.3)
    percy.snapshot(browser, "Admin logged in to homepage")

    # Finally logout
    assert browser.find_by_css('.globals a.logout').first.html == 'Abmelden'
    user_drop = browser.find_by_css('a.dropdown.user').first
    user_drop.mouse_over()
    logout_btn = browser.find_by_text('Abmelden')
    assert logout_btn.visible
    logout_btn.click()
    assert browser.is_text_present('Anmelden', wait_time=.25)
    assert browser.is_text_present('Sie wurden ausgeloggt.')
    percy.snapshot(browser, "Admin logged out")
