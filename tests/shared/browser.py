from __future__ import annotations

import json
import re
import shutil
import time

from datetime import datetime
from os import environ, system
from onegov.core.utils import module_path


from typing import overload, Any, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from collections.abc import Callable, Iterator
    from datetime import date
    from playwright.sync_api import (
        Browser, ConsoleMessage, ElementHandle, JSHandle, Locator, Page)


with open(module_path('tests.shared', 'drop_file.js')) as f:
    JS_DROP_FILE = f.read()


def _fill_locator(locator: Locator, value: str) -> None:
    """Fill a locator, handling file inputs and tab/newline key sequences."""
    input_type = locator.get_attribute('type')
    if input_type == 'file':
        assert locator.is_visible()
        assert locator.is_enabled()
        locator.set_input_files(value)
    elif '\t' in value:
        assert locator.is_visible()
        assert locator.is_enabled()
        # NOTE: We need to enter keys individually so tab completion in
        #       chosen select still works. This is a little fragile, since
        #       pressing Enter could result in the form being submitted
        #       in single line fields.
        for part in re.split(r'(\t|\n)', value):
            if part == '\t':
                locator.press('Tab')
            elif part == '\n':
                locator.press('Enter')
            else:
                locator.press_sequentially(part)
    else:
        locator.fill(value)


class PlaywrightElement:
    """
    Wraps a single Playwright Locator to provide a Splinter-like element API.
    """

    def __init__(self, locator: Locator) -> None:
        self._locator = locator

    def __getitem__(self, key: str) -> str | None:
        return self._locator.get_attribute(key)

    def click(self) -> None:
        self._locator.click()

    def fill(self, value: str) -> None:
        _fill_locator(self._locator, value)

    def select(self, value: str) -> None:
        self._locator.select_option(value)

    @property
    def text(self) -> str:
        return self._locator.text_content() or ''

    @property
    def value(self) -> str:
        try:
            return self._locator.input_value()
        except Exception:
            return self._locator.get_attribute('value') or ''

    @value.setter
    def value(self, value: str) -> None:
        self.fill(value)

    @property
    def checked(self) -> bool:
        return self._locator.is_checked()

    def is_visible(self) -> bool:
        return self._locator.is_visible()

    def scroll_to(self) -> None:
        self._locator.scroll_into_view_if_needed()

    def mouse_over(self) -> None:
        self._locator.hover()

    def find_by_value(self, value: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self._locator.locator(f'[value="{value}"]')
        )

    def find_by_text(self, text: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self._locator.get_by_text(text, exact=True)
        )

    def find_by_css(self, css: str) -> PlaywrightElementList:
        return PlaywrightElementList(self._locator.locator(css))

    def find_by_tag(self, tag: str) -> PlaywrightElementList:
        return PlaywrightElementList(self._locator.locator(tag))

    def find_by_name(self, name: str) -> PlaywrightElementList:
        return PlaywrightElementList(self._locator.locator(f'[name="{name}"]'))

    def find_by_id(self, element_id: str) -> PlaywrightElementList:
        return PlaywrightElementList(self._locator.locator(f'#{element_id}'))

    def find_by_xpath(self, xpath: str) -> PlaywrightElementList:
        return PlaywrightElementList(self._locator.locator(f'xpath={xpath}'))


class PlaywrightElementList:
    """Wraps a Playwright Locator as a Splinter-like ElementList.

    Proxies most calls to the first matched element, and supports indexing
    to access individual elements.
    """

    def __init__(self, locator: Locator) -> None:
        self._locator = locator

    def __len__(self) -> int:
        return self._locator.count()

    def __bool__(self) -> bool:
        return self._locator.count() > 0

    def __iter__(self) -> Iterator[PlaywrightElement]:
        for i in range(self._locator.count()):
            yield PlaywrightElement(self._locator.nth(i))

    @overload
    def __getitem__(self, index: int) -> PlaywrightElement: ...
    @overload
    def __getitem__(self, index: str) -> str | None: ...

    def __getitem__(self, index: int | str) -> PlaywrightElement | str | None:
        if isinstance(index, int):
            return PlaywrightElement(self._locator.nth(index))
        return self._locator.first.get_attribute(index)

    @property
    def first(self) -> PlaywrightElement:
        return PlaywrightElement(self._locator.first)

    def click(self) -> None:
        self._locator.first.click()

    def fill(self, value: str) -> None:
        _fill_locator(self._locator.first, value)

    def select(self, value: str) -> None:
        self._locator.first.select_option(value)

    @property
    def text(self) -> str:
        return self._locator.first.text_content() or ''

    @property
    def value(self) -> str:
        try:
            return self._locator.first.input_value()
        except Exception:
            return self._locator.first.get_attribute('value') or ''

    @value.setter
    def value(self, value: str) -> None:
        self.fill(value)

    @property
    def checked(self) -> bool:
        return self._locator.first.is_checked()

    def is_visible(self) -> bool:
        return self._locator.first.is_visible()

    def scroll_to(self) -> None:
        self._locator.first.scroll_into_view_if_needed()

    def mouse_over(self) -> None:
        self._locator.first.hover()

    def find_by_value(self, value: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self._locator.first.locator(f'[value="{value}"]')
        )

    def find_by_text(self, text: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self._locator.first.get_by_text(text, exact=True)
        )

    def find_by_css(self, css: str) -> PlaywrightElementList:
        return PlaywrightElementList(self._locator.first.locator(css))

    def find_by_tag(self, tag: str) -> PlaywrightElementList:
        return PlaywrightElementList(self._locator.first.locator(tag))

    def find_by_name(self, name: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self._locator.first.locator(f'[name="{name}"]')
        )

    def find_by_id(self, element_id: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self._locator.first.locator(f'#{element_id}')
        )

    def find_by_xpath(self, xpath: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self._locator.first.locator(f'xpath={xpath}')
        )


class FindLinks:
    """Provides Splinter-compatible browser.links.find_by_*() methods."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def find_by_href(self, href: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self.page.locator(f'//a[@href="{href}"]')
        )

    def find_by_partial_href(self, href: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self.page.locator(f'//a[contains(@href, "{href}")]')
        )

    def find_by_text(self, text: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self.page.get_by_role('link', name=text, exact=True)
        )

    def find_by_partial_text(self, text: str) -> PlaywrightElementList:
        return PlaywrightElementList(
            self.page.get_by_role('link', name=text, exact=False)
        )


class ExtendedBrowser:
    """Playwright-based browser providing OneGov-specific test helpers."""

    def __init__(
        self,
        browser: Browser,
        baseurl: str | None = None,
        wait_time: float = 2.0,
    ) -> None:
        self.baseurl = baseurl

        self.browser = browser
        self.context = browser.new_context()
        self._spawned_contexts = [self.context]

        self.page = page = self.context.new_page()
        self._links = FindLinks(page)

        self.wait_time = wait_time

        self._console_messages: list[tuple[str, str]] = []
        self._page_errors: list[str] = []
        page.on('console', self._on_console)
        page.on('pageerror', self._on_pageerror)

    @property
    def wait_time(self) -> float:
        return self._wait_time

    @wait_time.setter
    def wait_time(self, wait_time: float) -> None:
        self._wait_time = wait_time
        self.context.set_default_timeout(int(wait_time * 1000))

    def _on_console(self, msg: ConsoleMessage) -> None:
        if msg.type == 'error':
            level = 'SEVERE'
        elif msg.type == 'warning':
            level = 'WARNING'
        else:
            return  # ignore info/log/debug

        location = msg.location
        url = location.get('url', '') if location else ''
        text = msg.text
        formatted = f"{url} - {text}" if url else text

        self._console_messages.append((level, formatted))

    def _on_pageerror(self, exc: Exception) -> None:
        self._page_errors.append(str(exc))

    def _clear_console(self) -> None:
        self._console_messages.clear()
        self._page_errors.clear()

    def spawn(self) -> ExtendedBrowser:
        """Spawn a new browser instance with its own context"""
        instance = ExtendedBrowser(self.browser, self.baseurl)
        instance._spawned_contexts = self._spawned_contexts
        self._spawned_contexts.append(instance.context)
        return instance

    @property
    def links(self) -> FindLinks:
        return self._links

    @property
    def html(self) -> str:
        return self.page.content()

    @property
    def url(self) -> str:
        return self.page.url

    def visit(
        self,
        url: str,
        sleep_before_fail: float = 0,
        expected_errors: list[dict[str, Any]] | None = None,
        ignore_all_console_errors: bool = False
    ) -> None:
        """Navigate to *url* and optionally check for console errors.

        If *url* is relative and ``self.baseurl`` is set the two are joined.
        """
        self._clear_console()
        if self.baseurl and not url.startswith('http'):
            url = self.baseurl.rstrip('/') + url
        # NOTE: Since application startup can take a while we use a different
        #       timeout for page navigation, that's a little higher.
        self.page.goto(url, timeout=30000)
        if not ignore_all_console_errors:
            self.fail_on_console_errors(sleep_before_fail, expected_errors)

    def login(
        self,
        username: str,
        password: str,
        to: str | None = None
    ) -> None:
        url = '/auth/login' + (to and ('/?to=' + to) or '')
        self.visit(url)
        self.page.fill('input[name="username"]', username)
        self.page.fill('input[name="password"]', password)
        self.page.click('form input[type="submit"]')

    def login_admin(self, to: str | None = None) -> None:
        self.login('admin@example.org', 'hunter2', to)

    def login_editor(self, to: str | None = None) -> None:
        self.login('editor@example.org', 'hunter2', to)

    def login_member(self, to: str | None = None) -> None:
        self.login('member@example.org', 'hunter2', to)

    def logout(self) -> None:
        self.visit('/auth/logout')

    def fill(self, name: str, value: Any) -> None:
        """Fill the first form field with the given *name* attribute."""
        # File input
        file_input = self.page.locator(f'input[type="file"][name="{name}"]')
        if file_input.count() > 0:
            file_input.first.set_input_files(value)
            return

        # Checkbox
        checkbox = self.page.locator(
            f'input[type="checkbox"][name="{name}"]'
        )
        if checkbox.count() > 0:
            if value:
                checkbox.first.check()
            else:
                checkbox.first.uncheck()
            return

        # Radio button
        radio = self.page.locator(
            f'input[type="radio"][name="{name}"]'
        )
        if radio.count() > 0:
            radio.locator(f'[value="{value}"]').check()
            return

        # Select element
        select_el = self.page.locator(f'select[name="{name}"]')
        if select_el.count() > 0:
            select_el.first.select_option(str(value))
            return

        # Text-like input or textarea
        field = self.page.locator(
            f'input[name="{name}"],textarea[name="{name}"]'
        ).first
        if isinstance(value, dict):
            value = json.dumps(value, indent=2)
        else:
            value = str(value)
        _fill_locator(field, value)

    def fill_form(self, data: dict[str, Any]) -> None:
        """Fill multiple form fields given a ``{name: value}`` mapping."""
        for name, value in data.items():
            self.fill(name, value)

    def choose(self, name: str, value: str) -> None:
        """Select a radio button identified by *name* and *value*."""
        self.page.locator(
            f'input[type="radio"][name="{name}"][value="{value}"]'
        ).check()

    def find_by_css(self, css: str) -> PlaywrightElementList:
        return PlaywrightElementList(self.page.locator(css))

    def find_by_value(self, value: str) -> PlaywrightElementList:
        return PlaywrightElementList(self.page.locator(f'[value="{value}"]'))

    def find_by_text(self, text: str) -> PlaywrightElementList:
        return PlaywrightElementList(self.page.get_by_text(text, exact=True))

    def find_by_tag(self, tag: str) -> PlaywrightElementList:
        return PlaywrightElementList(self.page.locator(tag))

    def find_by_name(self, name: str) -> PlaywrightElementList:
        return PlaywrightElementList(self.page.locator(f'[name="{name}"]'))

    def find_by_id(self, element_id: str) -> PlaywrightElementList:
        return PlaywrightElementList(self.page.locator(f'#{element_id}'))

    def find_by_xpath(self, xpath: str) -> PlaywrightElementList:
        return PlaywrightElementList(self.page.locator(f'xpath={xpath}'))

    def is_text_present(
        self,
        text: str,
        wait_time: float | None = None
    ) -> bool:
        if wait_time is None:
            wait_time = self.wait_time
        try:
            self.page.get_by_text(text, exact=False).first.wait_for(
                timeout=int(wait_time * 1000)
            )
            return True
        except Exception:
            return False

    def is_element_present_by_css(
        self,
        css: str,
        wait_time: float | None = None
    ) -> bool:
        if wait_time is None:
            wait_time = self.wait_time
        try:
            self.page.locator(css).first.wait_for(
                timeout=int(wait_time * 1000)
            )
            return True
        except Exception:
            return False

    def is_element_present_by_id(self, element_id: str) -> bool:
        return self.page.locator(f'#{element_id}').count() > 0

    def is_element_present_by_name(self, name: str) -> bool:
        return self.page.locator(f'[name={name}]').count() > 0

    def is_element_present_by_xpath(
        self,
        xpath: str,
        wait_time: float | None = None
    ) -> bool:
        if wait_time is None:
            wait_time = self.wait_time
        try:
            self.page.locator(f'xpath={xpath}').first.wait_for(
                timeout=int(wait_time * 1000)
            )
            return True
        except Exception:
            return False

    def execute_script(self, script: str, *args: Any) -> Any:
        """Execute *script* in the browser, optionally passing *args*.

        Arguments are mapped to ``arguments[0]``, ``arguments[1]``, … inside
        the script, matching Selenium's convention.
        """
        if args:
            wrapped = f"(args) => {{ var arguments = args; {script} }}"
            return self.page.evaluate(wrapped, list(args))
        return self.page.evaluate(f"() => {{ {script} }}")

    def evaluate_script(self, expression: str) -> Any:
        return self.page.evaluate(expression)

    def wait_for_js_variable(
        self,
        variable: str,
        timeout: float = 10.0
    ) -> None:
        """Block until the named JavaScript variable is defined."""
        self.page.wait_for_function(
            f'() => typeof {variable} !== "undefined"',
            timeout=int(timeout * 1000)
        )

    def wait_for(
        self,
        condition: Callable[[], bool],
        timeout: float = 10.0
    ) -> bool:
        """Poll *condition* until it returns ``True`` or *timeout* elapses."""
        if not callable(condition):
            raise ValueError("The condition must be a callable object.")

        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if condition():
                return True
            time.sleep(0.05)
        raise TimeoutError("Timeout reached")

    def interact_with_ace_editor(
        self,
        content: str | dict[str, Any],
        name: str | None = None
    ) -> None:
        """Type *content* into the Ace editor widget on the current page."""
        if isinstance(content, dict):
            content = json.dumps(content, indent=2)

        self.page.locator(
            f'{f".field-{name} " if name else ''}.ace_editor'
        ).click()

        # Clear existing content
        self.page.keyboard.press('Control+a')
        self.page.keyboard.press('Delete')
        time.sleep(0.1)

        ends_with_brace = content.rstrip().endswith('}')
        typing_content = content[:-1] if ends_with_brace else content
        self.page.keyboard.type(typing_content)

        if ends_with_brace:
            self.page.keyboard.type('}')
            time.sleep(0.1)
            # Remove the auto-inserted closing brace from the editor
            self.page.keyboard.press('Backspace')

        # Blur the editor to trigger any change handlers
        self.page.locator('body').click()

    def set_datetime_element(
        self,
        selector: str,
        date_or_time: datetime | date
    ) -> None:
        """Set the value of a datetime-local or date input via JavaScript."""
        if isinstance(date_or_time, datetime):
            value = date_or_time.strftime("%Y-%m-%dT%H:%M")
        else:
            value = date_or_time.strftime("%Y-%m-%d")

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
        self.execute_script(script, selector, value)

    def scroll_to_css(self, css: str) -> None:
        """Scroll the first element matching *css* into view."""
        self.execute_script(
            f'document.querySelector("{css}").scrollIntoView()'
        )

    def drop_file(self, selector: str, path: StrPath) -> None:
        """Simulate dropping *path* onto the element matched by *selector*.

        Uses the same JS helper as the legacy Selenium implementation
        (drop_file.js) which creates a hidden file input, then uses
        Playwright's set_input_files to trigger the drag/drop events.
        """
        # Obtain an ElementHandle so we can pass it directly into JS.
        element: ElementHandle | None = (
            self.page.locator(selector).first.element_handle()
        )
        if element is None:
            raise RuntimeError(
                f"drop_file: no element found for selector {selector!r}"
            )

        # Wrap drop_file.js so the element is passed as arguments[0].
        # Use a regular (non-arrow) anonymous function to make the local
        # ``arguments`` variable shadow the built-in safely.
        wrapped_js = (
            "(function(dropzone) {"
            "    var arguments = [dropzone, undefined, undefined];"
            f"   {JS_DROP_FILE}"
            "})"
        )

        file_input_handle: JSHandle = self.page.evaluate_handle(
            wrapped_js, element
        )

        file_input: ElementHandle | None = file_input_handle.as_element()
        if file_input is None:
            raise RuntimeError("drop_file: JS did not return an element")

        file_input.set_input_files(str(path))

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
            dict(
                level='WARNING',
                rgxp=re.escape('https://web.cmp.usercentrics.eu')
            ),
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
            time.sleep(sleep_before)
        assert not error_msgs, error_msgs

    def get_console_log(
        self,
        filters: list[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """Return console errors/warnings, optionally applying *filters*.

        Each filter is a dict whose keys narrow down which messages to exclude.
        Supported keys: ``level`` (``'SEVERE'``/``'WARNING'``), ``rgxp``
        (regex matched against the message text), and ``source`` (ignored –
        Playwright does not expose the same source categories as ChromeDevTools
        via Selenium, so the rgxp/level constraints are sufficient).
        """
        messages: list[dict[str, Any]] = []

        for level, text in self._console_messages:
            messages.append({
                'level': level,
                'source': 'console-api',
                'message': text,
            })

        for error_text in self._page_errors:
            messages.append({
                'level': 'SEVERE',
                'source': 'javascript',
                'message': error_text,
            })

        if not messages:
            return []

        filters = filters or []

        def apply_filter(fil: dict[str, Any], item: dict[str, Any]) -> bool:
            checks = []
            for k, v in fil.items():
                if k == 'source':
                    # Playwright does not separate console messages by source
                    # category (network / security / console-api) the same way
                    # Selenium/CDP does. Skip the source check so the rgxp and
                    # level constraints still take effect.
                    pass
                elif k == 'rgxp':
                    checks.append(bool(re.search(v, item['message'])))
                else:
                    checks.append(item.get(k) == v)
            # A filter with only a ``source`` key has no remaining checks and
            # should not match anything.
            return bool(checks) and all(checks)

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
        log = self.get_console_log(filters)
        return '\n'.join(f"{i['level']}: {i['message']}" for i in log)


def screen_shot(
    name: str,
    browser: ExtendedBrowser,
    open_file: bool = True
) -> None:
    file = f'/tmp/{name}.png'
    browser.page.screenshot(path=file, full_page=True)
    if not open_file:
        return
    programs = ('xviewer',)
    for p in programs:
        if shutil.which(p):
            system(f'{p} {file} &')
