"""
Integration of percy by Browserstack

There are two modes:
- running in CI
- running locally

"""
from percy import percy_snapshot


class PercySnapshot:

    def snapshot(self, browser, message):
        app = browser.app_name
        msg = f"{app.capitalize()}: {message.capitalize()}"
        percy_snapshot(
            driver=browser.driver,
            name=msg
        )
