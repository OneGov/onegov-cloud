from __future__ import annotations

import json
import os
import re

from functools import cached_property
from pyquery import PyQuery as pq  # type: ignore[import-untyped]


from typing import Any, Generic, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.framework import Framework
    from onegov.core.types import EmailJsonDict
    from typing import type_check_only, TypeVar
    from webtest.app import TestApp as BaseTestApp
    from webtest.response import _Pattern, TestResponse
    from webtest.forms import Form

    _AppT = TypeVar('_AppT', bound=Framework, default=Framework)
    BaseExtension = TestResponse
    class TestApp(BaseTestApp['ExtendedResponse', _AppT]):
        ...
else:
    from typing import TypeVar
    from webtest import TestApp as BaseTestApp

    _AppT = TypeVar('_AppT')
    BaseExtension = object
    class TestApp(BaseTestApp, Generic[_AppT]):
        ...



EXTRACT_HREF = re.compile(
    r'(?:href|ic-get-from|ic-post-to|ic-delete-from)="([^"]+)')


class Client(TestApp[_AppT]):
    skip_n_forms = False
    use_intercooler = False

    def spawn(self) -> Self:
        """ Spawns a new client that points to the same app.

        All login data / cookies are lost.

        """

        return self.__class__(self.app)

    def login(
        self,
        username: str,
        password: str,
        to: str | None = None
    ) -> ExtendedResponse:
        """ Login a user through the usualy /auth/login path. """

        url = '/auth/login' + (to and ('/?to=' + to) or '')

        login_page = self.get(url)
        login_page.form.set('username', username)
        login_page.form.set('password', password)
        return login_page.form.submit()

    def login_admin(self, to: str | None = None) -> ExtendedResponse:
        return self.login('admin@example.org', 'hunter2', to)

    def login_editor(self, to: str | None = None) -> ExtendedResponse:
        return self.login('editor@example.org', 'hunter2', to)

    def login_supporter(self, to: str | None = None) -> ExtendedResponse:
        return self.login('supporter@example.org', 'hunter2', to)

    def login_member(self, to: str | None = None) -> ExtendedResponse:
        return self.login('member@example.org', 'hunter2', to)

    def logout(self) -> ExtendedResponse:
        return self.get('/auth/logout')

    def get_email(
        self,
        batch_index: int,
        index: int = 0,
        flush_queue: bool = False
    ) -> EmailJsonDict | None:
        """ Get the nth email from the batch at the given batch index.
        This will be dictionary formatted to suit the Postmark API

        :param flush_queue: Should the email queue be emptied after
            retrieving the email?

        See: https://postmarkapp.com/developer/api/email-api
        """
        assert hasattr(self.app, 'maildir')
        files = [
            os.path.join(self.app.maildir, p)
            for p in os.listdir(self.app.maildir)
        ]
        if not files:
            return None

        # sort by modtime so we're immune to freezegun shenanigans
        files = sorted(files, key=lambda f: os.path.getmtime(f))
        with open(files[batch_index]) as fp:
            messages = json.loads(fp.read())

        if flush_queue:
            for file in files:
                os.remove(file)
        return messages[index]

    def flush_email_queue(self) -> None:
        assert hasattr(self.app, 'maildir')
        for path in os.listdir(self.app.maildir):
            os.remove(os.path.join(self.app.maildir, path))

    def extract_href(self, link: str) -> str | None:
        """ Takes a link (<a href...>) and returns the href address. """

        result = EXTRACT_HREF.search(link)
        return result and result.group(1) or None

    def extend_response(self, response: TestResponse) -> ExtendedResponse:
        """ Takes the default response and adds additional methods/properties,
        or overrides them.

        """
        bases: list[type[object]] = [GenericResponseExtension]

        if self.skip_n_forms:
            bases.append(type(
                "SkipNForms",
                (SkipNFormsExtension, ),
                dict(n=self.skip_n_forms)
            ))

        if self.use_intercooler:
            bases.append(IntercoolerClickExtension)

        bases.append(response.__class__)
        response.__class__ = type('ExtendedResponse', tuple(bases), {})

        return response  # type: ignore[return-value]

    if not TYPE_CHECKING:
        def do_request(self, *args, **kwargs):
            """ Dirtily inject extra methods into the response -> done this way
            because not all testclients support overriding the response class
            (i.e. webtest-selenium).

            """

            return self.extend_response(super().do_request(*args, **kwargs))


class GenericResponseExtension(BaseExtension):

    def select_checkbox(
        self,
        groupname: str,
        label: str,
        form: Form[Self] | None = None,
        checked: bool = True,
        limit: int | None = None
    ) -> None:
        """ Selects one of many checkboxes by fuzzy searching the label next to
        it. Webtest is not good enough in this regard.

        Selects the checkbox from the form returned by page.form, or the given
        form if passed. In any case, the form needs to be part of the page.

        A limit can be set to restrict the number of checkboxes to select.

        """

        elements = self.pyquery(f'input[name="{groupname}"]')

        if not elements:
            raise KeyError(f"No input named {groupname} found")

        form = form or self.form
        count = 0

        for ix, el in enumerate(elements):
            if label in el.label.text_content():
                form.get(groupname, index=ix).value = checked
                count += 1
                if limit is not None and count >= limit:
                    break

    def select_radio(
        self,
        groupname: str,
        label: str,
        form: Form[Self] | None = None
    ) -> None:
        """ Like `select_checkbox`, but with the ability to select a radio
        button by the name of its label.

        """

        elements = self.pyquery(f'input[name="{groupname}"]')

        if not elements:
            raise KeyError(f"No input named {groupname} found")

        form = form or self.form

        for el in elements:
            if label in el.label.text_content():
                form.get(groupname).value = el.values()[-1]
                break

    @cached_property
    def pyquery(self) -> pq:
        """ Webtests property of the same name seems to not work on all
        pages (it uses self.testbody and not self.body) and it also doesn't
        cache the result, which is an easy way to improve some lookups here.

        """
        return pq(self.body)

    def __or__(self, text: str) -> str:
        """ Grep style searching the response, e.g.
        `print(client.get('/') | 'Text')`

        """
        return '\n'.join(l for l in str(self).split('\n') if text in l)


class SkipNFormsExtension(BaseExtension):
    n = 0

    @property
    def form(self) -> Form[Self]:
        """ Use Form with ID 'main-form', else ignore the first n forms.

        """
        if 'main-form' in self.forms:
            return self.forms['main-form']

        if self.n in self.forms:
            return self.forms[self.n]
        else:
            return super().form


class IntercoolerClickExtension(BaseExtension):

    def click(
        self,
        description: _Pattern | None = None,
        linkid: _Pattern | None = None,
        href: _Pattern | None = None,
        index: int | None = None,
        verbose: bool = False,
        extra_environ: dict[str, Any] | None = None,
    ) -> Self:
        """ Adds intercooler.js support for links (by description). """
        try:
            return super().click(
                description, linkid, href, index, verbose, extra_environ)
        except IndexError as exception:
            result = self.find_ic_url(
                description, linkid, href, index, verbose)

            if not result:
                raise

            method, url = result

            if method == 'get':
                return self.test_app.get(url, extra_environ=extra_environ)
            elif method == 'post':
                return self.test_app.post(url, extra_environ=extra_environ)
            elif method == 'delete':
                return self.test_app.delete(url, extra_environ=extra_environ)
            else:
                raise NotImplementedError from exception

    def find_ic_url(self,
        description: _Pattern | None,
        linkid: _Pattern | None,
        href: _Pattern | None,
        index: int | None,
        verbose: bool
    ) -> tuple[str, str] | None:

        attrs = (
            ('post', 'ic-post-to'),
            ('delete', 'ic-delete-from'),
            ('get', 'ic-get-from'),
        )

        for method, attr in attrs:
            url = self._find_ic_url_by_attr(
                attr=attr,
                content=description,
                href_extract=None,
                id=linkid,
                href_pattern=href,
                index=index,
                verbose=verbose)

            if url:
                return method, url
        return None

    def _find_ic_url_by_attr(self, attr: str, **kwargs: Any) -> str | None:
        try:
            html, desc, attrs = self._find_element(  # type: ignore[attr-defined]
                tag='a', href_attr=attr, **kwargs)

            return attrs[attr]
        except IndexError:
            return None

if TYPE_CHECKING:
    @type_check_only
    class ExtendedResponse(
        GenericResponseExtension,
        SkipNFormsExtension,
        IntercoolerClickExtension,
        TestResponse
    ): ...
