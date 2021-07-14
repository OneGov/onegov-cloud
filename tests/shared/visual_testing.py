"""
Integration of percy by Browserstack

There are two modes:
- running in CI
- running locally

"""
from os import environ
from percy import percy_snapshot


class PercySnapshot:

    def __init__(self):
        environ.setdefault('PERCY_BRANCH', 'local')

    def app_name(self, baseurl):
        return baseurl.split('/')[-1]

    def snapshot(self, browser, message):
        msg = f"{self.app_name(browser.baseurl)} - {message.capitalize()}"
        percy_snapshot(
            driver=browser.driver,
            name=msg
        )
