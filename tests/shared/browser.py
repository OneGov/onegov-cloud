from os import environ, system
import re
import shutil
import time

from contextlib import suppress
from http.client import RemoteDisconnected
from onegov.core.utils import module_path
from time import sleep


with open(module_path('tests.shared', 'drop_file.js')) as f:
    JS_DROP_FILE = f.read()


class InjectedBrowserExtension(object):
    """ Offers methods to inject an extended browser into the Splinter browser
    class hierarchy. All methods not related to spawning/cloning a new browser
    instance are provided by :class:`ExtendedBrowser`.

    """

    @classmethod
    def spawn(cls, browser_factory, *args, **kwargs):
        """ Takes a Splinter browser factory together with the arguments
        meant for the factory and returns a new browser with the current class
        injected into the class hierarchy.

        """

        # spawning Chrome on Travis is rather flaky and succeeds less than
        # 50% of the time for unknown reasons
        for _ in range(10):
            with suppress(Exception):
                browser = browser_factory(*args, **kwargs)
                break
            sleep(0.5)
        else:
            browser = browser_factory(*args, **kwargs)

        class LeechedExtendedBrowser(cls, browser.__class__):

            clones = []

            def quit(self):
                for clone in self.clones:
                    with suppress(RemoteDisconnected):
                        clone.quit()

                with suppress(RemoteDisconnected):
                    super().quit()

        browser.spawn_parameters = cls, browser_factory, args, kwargs
        browser.__class__ = LeechedExtendedBrowser
        return browser

    def clone(self):
        """ Returns an independent instance of the current browser (all state
        is reset on the new instance).

        """

        cls, browser_factory, args, kwargs = self.spawn_parameters
        browser = cls.spawn(browser_factory, *args, **kwargs)

        self.clones.append(browser)

        for key, value in self.clone_parameters.items():
            setattr(browser, key, value)

        return browser

    @property
    def clone_parameters(self):
        """ Returns a dictionary of values that need to be applied to the new
        browser instance after it is cloned.

        """
        return {}


class ExtendedBrowser(InjectedBrowserExtension):
    """ Extends Splinter's browser with OneGov specific methods.

    """

    # Prefix appended to urls without http prefix.
    baseurl = None

    @property
    def clone_parameters(self):
        return {
            'baseurl': self.baseurl
        }

    def visit(
            self, url, sleep_before_fail=0, expected_errors=None
    ):
        """ Overrides the default visit method to provided baseurl support.
            halt_on_fail keeps the browser window open for some minutes
            before failing the test.
            Use expected_errors as filters to pass the test.
         """
        if self.baseurl and not url.startswith('http'):
            url = self.baseurl.rstrip('/') + url

        page = super().visit(url)
        self.fail_on_console_errors(sleep_before_fail, expected_errors)
        return page

    def login(self, username, password, to=None):
        """ Login a user through the usualy /auth/login path. """

        url = '/auth/login' + (to and ('/?to=' + to) or '')

        self.visit(url)
        self.fill('username', username)
        self.fill('password', password)
        self.find_by_css('form input[type="submit"]').first.click()

    def login_admin(self, to=None):
        self.login('admin@example.org', 'hunter2', to)

    def login_editor(self, to=None):
        self.login('editor@example.org', 'hunter2', to)

    def logout(self):
        self.visit('/auth/logout')

    def wait_for_js_variable(self, variable, timeout=10.0):
        """ Wait until the given javascript variable is no longer undefined """

        time_budget = timeout
        interval = 0.1

        is_undefined = f'{variable} == undefined'

        while time_budget > 0 and self.evaluate_script(is_undefined):
            time.sleep(interval)
            time_budget -= interval

        if time_budget <= 0:
            raise RuntimeError("Timeout reached")

    def scroll_to_css(self, css):
        """ Scrolls to the first element matching the given css expression. """

        self.execute_script(
            'document.querySelector("{}").scrollIntoView()'.format(css))

    def drop_file(self, selector, path):
        # https://gist.github.com/z41/c11f8a4072e9f67e5755d4a1a72c8f02
        dropzone = self.find_by_css(selector)[0]._element

        input = self.driver.execute_script(JS_DROP_FILE, dropzone)
        input.send_keys(str(path))

    @property
    def failsafe_filters(self):
        return [
            dict(source='security', rgxp="Content Security Policy"),
            dict(source='security', rgxp="Refused to connect"),
            dict(source='network', rgxp="favicon.ico"),
            dict(source='console-api', rgxp="crbug/1173575"),
            dict(level='WARNING', rgxp="facebook"),
            dict(level='WARNING', rgxp=re.escape('react-with-addons.js')), # forms app
            dict(level='SEVERE', rgxp=re.escape("api.mapbox.com")),
        ]

    def fail_on_console_errors(self, sleep_before=0, expected_errors=None):
        expected_errors = expected_errors or []
        filters = expected_errors + self.failsafe_filters
        error_msgs = self.get_console_log(filters)
        if error_msgs and environ.get('SHOW_BROWSER') == '1':
            sleep(sleep_before)
        assert not error_msgs, error_msgs

    def get_console_log(self, filters=None):
        """
        Get the browsers console log.
        Filter the message by using filters. The filter excludes the entry
        if all criteria apply.
        Filters have the form of the message itself excep for the rgxp key:

        {'source': 'security', 'level': 'SEVERE'}
        {'level': 'WARNING'}
        {'level': 'SEVERE', 'rgxp': 'Content Security Policy'}

        Use a regex expression to filter by the message of the error
        """
        messages = self.driver.get_log('browser')
        if not messages:
            return []

        filters = filters or []

        def apply_filter(fil, item):
            checks = []
            for k, v in fil.items():
                if k == 'rgxp':
                    checks.append(
                        re.search(v, item['message']) and True or False
                    )
                else:
                    checks.append(item.get(k) == v)
            return all(checks)

        def include(item):
            for fil in filters:
                if apply_filter(fil, item):
                    return False
            return True

        return [item for item in messages if include(item)]

    def console_log(self, filters=None):
        console_log = self.get_console_log(filters)
        return "\n".join(
            (f"{i['level']}: {i['message']}" for i in console_log)
        )


def screen_shot(name, browser, open_file=True):
    file = browser.screenshot(f'/tmp/{name}.png', full=True)
    if not open_file:
        return
    programs = ('xviewer', )
    for p in programs:
        if shutil.which(p):
            system(f'{p} {file} &')
