from __future__ import annotations

import json
from os import environ, system
import datetime
import re
import shutil
import time
from contextlib import suppress
from http.client import RemoteDisconnected
from onegov.core.utils import module_path
from selenium.webdriver import ActionChains, Keys
from time import sleep


from typing import cast, Any, ParamSpec, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime, date
    from os import PathLike
    from selenium.webdriver import Chrome
    from splinter import Browser
else:
    Browser = object

P = ParamSpec('P')


with open(module_path('tests.shared', 'drop_file.js')) as f:
    JS_DROP_FILE = f.read()


class InjectedBrowserExtension(Browser):
    """ Offers methods to inject an extended browser into the Splinter browser
    class hierarchy. All methods not related to spawning/cloning a new browser
    instance are provided by :class:`ExtendedBrowser`.

    """

    driver: Chrome
    clones: list[Self]
    spawn_parameters: tuple[
        type[Self],
        Callable[..., Browser],
        tuple[Any, ...],
        dict[str, Any]
    ]

    @classmethod
    def spawn(
        cls,
        browser_factory: Callable[P, Browser],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> Self:
        """ Takes a Splinter browser factory together with the arguments
        meant for the factory and returns a new browser with the current class
        injected into the class hierarchy.

        """

        browser: Browser

        # spawning Chrome on Travis is rather flaky and succeeds less than
        # 50% of the time for unknown reasons
        for _ in range(10):
            with suppress(Exception):
                browser = browser_factory(*args, **kwargs)
                break
            sleep(0.5)
        else:
            browser = browser_factory(*args, **kwargs)

        class LeechedExtendedBrowser(cls, browser.__class__):  # type: ignore

            clones: list[Self] = []

            def quit(self) -> None:
                for clone in self.clones:
                    with suppress(RemoteDisconnected):
                        clone.quit()

                with suppress(RemoteDisconnected):
                    super().quit()

        browser = cast('Self', browser)
        browser.spawn_parameters = cls, browser_factory, args, kwargs
        browser.__class__ = LeechedExtendedBrowser
        return browser

    def clone(self) -> Self:
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
    def clone_parameters(self) -> dict[str, Any]:
        """ Returns a dictionary of values that need to be applied to the new
        browser instance after it is cloned.

        """
        return {}


class ExtendedBrowser(InjectedBrowserExtension):
    """ Extends Splinter's browser with OneGov specific methods.

    """

    # Prefix appended to urls without http prefix.
    baseurl: str | None = None

    @property
    def clone_parameters(self) -> dict[str, Any]:
        return {
            'baseurl': self.baseurl
        }

    def visit(
        self,
        url: str,
        sleep_before_fail: float = 0,
        expected_errors: list[dict[str, Any]] | None = None,
        ignore_all_console_errors: bool = False
    ) -> None:
        """ Overrides the default visit method to provided baseurl support.
            halt_on_fail keeps the browser window open for some minutes
            before failing the test.
            Use expected_errors as filters to pass the test.
         """
        if self.baseurl and not url.startswith('http'):
            url = self.baseurl.rstrip('/') + url

        super().visit(url)
        if not ignore_all_console_errors:
            self.fail_on_console_errors(sleep_before_fail, expected_errors)

    def login(
        self,
        username: str,
        password: str,
        to: str | None = None
    ) -> None:
        """ Login a user through the usualy /auth/login path. """

        url = '/auth/login' + (to and ('/?to=' + to) or '')

        self.visit(url)
        self.fill('username', username)
        self.fill('password', password)
        self.find_by_css('form input[type="submit"]').first.click()

    def login_admin(self, to: str | None = None) -> None:
        self.login('admin@example.org', 'hunter2', to)

    def login_editor(self, to: str | None = None) -> None:
        self.login('editor@example.org', 'hunter2', to)

    def login_member(self, to: str | None = None) -> None:
        self.login('member@example.org', 'hunter2', to)

    def logout(self) -> None:
        self.visit('/auth/logout')

    def wait_for_js_variable(
        self,
        variable: str,
        timeout: float = 10.0
    ) -> None:
        """ Wait until the given javascript variable is no longer undefined """

        time_budget = timeout
        interval = 0.1

        def undefined() -> bool:
            try:
                return self.evaluate_script(f'{variable} == undefined')
            except Exception as exception:
                if 'not defined' in str(exception):
                    return True
                raise exception

        while time_budget > 0 and undefined():
            time.sleep(interval)
            time_budget -= interval

        if time_budget <= 0:
            raise RuntimeError("Timeout reached")

    def wait_for(
        self,
        condition: Callable[[], bool],
        timeout: float = 10.0
    ) -> bool:
        """Wait until the condition is satisfied or timeout is reached."""

        if not callable(condition):
            raise ValueError("The condition must be a callable object.")

        time_budget = timeout
        interval = 0.1

        while time_budget > 0:
            if condition():
                return True

            time.sleep(interval)
            time_budget -= interval

        raise TimeoutError("Timeout reached")

    def interact_with_ace_editor(self, content: str | dict[str, Any]) -> None:
        # I actually tried setting the value with js, (would be much simpler)
        # while this die made text appear in the ace editor field,  it wasn't
        # actually truly set, probably due to some intricacies of ace.
        # So we just type it out letter by letter.

        if isinstance(content, dict):
            content = json.dumps(content, indent=2)

        editor_element = self.find_by_css('.ace_editor')
        editor_element.click()

        # Clear existing content (Ctrl+A, Delete)
        actions = ActionChains(self.driver)
        actions.key_down(Keys.CONTROL).send_keys('a').key_up(
            Keys.CONTROL
        ).send_keys(Keys.DELETE).perform()
        time.sleep(0.1)

        ends_with_brace = content.rstrip().endswith('}')
        # Type the content - but if it ends with a closing brace,
        # omit the last character
        typing_content = content[:-1] if ends_with_brace else content
        actions = ActionChains(self.driver)
        actions.send_keys(typing_content).perform()

        # If we omitted the closing brace, add it now and immediately press
        # Backspace to remove any auto-inserted closing brace
        if ends_with_brace:
            actions = ActionChains(self.driver)
            actions.send_keys('}').perform()
            time.sleep(0.1)

            # Press Backspace to remove the auto-inserted second closing brace
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.BACKSPACE).perform()

        # Click somewhere else to ensure the editor loses focus and updates
        self.find_by_tag('body').click()

    def set_datetime_element(
        self, selector: str, date_or_time: datetime | date
    ) -> None:
        """ Sets the date and time on a datetime-local field directly by
        setting its value.
        """

        # The way we have determined this pattern is inspecting the DOM
        # element of the datetime picker and seeing what kind of format it
        # expects:
        # document.getElementById('publication_start').value;
        if isinstance(date_or_time, datetime.datetime):
            date_or_time = date_or_time.strftime("%Y-%m-%dT%H:%M")
        else:
            date_or_time = date_or_time.strftime("%Y-%m-%d")

        script = """
            function setDateTimeDirect(selector, dateTimeString) {
                const element = document.querySelector(selector);
                if (!element) {
                    console.error('Datetime field with selector "' + selector +
                        '" not found.');
                    return;
                }
                element.value = dateTimeString;
                element.dispatchEvent(new Event('input', {
                    'bubbles': true,
                    'cancelable': true
                }));
                element.dispatchEvent(new Event('change', {
                    'bubbles': true,
                    'cancelable': true
                }));
            }
            setDateTimeDirect(arguments[0], arguments[1]);
        """

        self.execute_script(script, selector, date_or_time)

    def scroll_to_css(self, css: str) -> None:
        """ Scrolls to the first element matching the given css expression. """

        self.execute_script(
            'document.querySelector("{}").scrollIntoView()'.format(css))

    def drop_file(self, selector: str, path: PathLike[str]) -> None:
        # https://gist.github.com/z41/c11f8a4072e9f67e5755d4a1a72c8f02
        dropzone = self.find_by_css(selector)[0]._element  # type: ignore[attr-defined]

        input = self.driver.execute_script(JS_DROP_FILE, dropzone)  # type: ignore[no-untyped-call]
        input.send_keys(str(path))

    @property
    def failsafe_filters(self) -> list[dict[str, Any]]:
        return [
            dict(source='security', rgxp="Content Security Policy"),
            dict(source='security', rgxp="Refused to connect"),
            dict(source='network', rgxp="favicon.ico"),
            dict(source='console-api', rgxp="crbug/1173575"),
            dict(level='WARNING', rgxp="facebook"),
            dict(level='WARNING', rgxp="Third-party cookie will be blocked"),
            dict(level='WARNING', rgxp=re.escape('react-with-addons.js')),
            dict(level='SEVERE', rgxp=re.escape("api.mapbox.com")),
        ]

    def fail_on_console_errors(
        self,
        sleep_before: float = 0,
        expected_errors: list[dict[str, Any]] | None = None
    ) -> None:
        expected_errors = expected_errors or []
        filters = expected_errors + self.failsafe_filters
        error_msgs = self.get_console_log(filters)
        if error_msgs and environ.get('SHOW_BROWSER') == '1':
            sleep(sleep_before)
        assert not error_msgs, error_msgs

    def get_console_log(
        self,
        filters: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
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
        messages = self.driver.get_log('browser')  # type: ignore[no-untyped-call]
        if not messages:
            return []

        filters = filters or []

        def apply_filter(fil: dict[str, Any], item: dict[str, Any]) -> bool:
            checks = []
            for k, v in fil.items():
                if k == 'rgxp':
                    checks.append(
                        re.search(v, item['message']) and True or False
                    )
                else:
                    checks.append(item.get(k) == v)
            return all(checks)

        def include(item: dict[str, Any]) -> bool:
            for fil in filters:
                if apply_filter(fil, item):
                    return False
            return True

        return [item for item in messages if include(item)]

    def console_log(
        self,
        filters: list[dict[str, Any]] | None = None
    ) -> str:
        console_log = self.get_console_log(filters)
        return "\n".join(
            (f"{i['level']}: {i['message']}" for i in console_log)
        )


def screen_shot(name: str, browser: Browser, open_file: bool = True) -> None:
    file = browser.screenshot(f'/tmp/{name}.png', full=True)
    if not open_file:
        return
    programs = ('xviewer', )
    for p in programs:
        if shutil.which(p):
            system(f'{p} {file} &')
