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
        self.inactive = environ.get('PERCY_TOKEN') and False or True

    def snapshot(self, browser, message):
        if self.inactive:
            return
        app = browser.app_name
        msg = f"{app.capitalize()}: {message.capitalize()}"
        percy_snapshot(
            driver=browser.driver,
            name=msg
        )
