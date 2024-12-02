import json
import os
import re

from functools import cached_property
from pyquery import PyQuery as pq
from webtest import TestApp

EXTRACT_HREF = re.compile(
    r'(?:href|ic-get-from|ic-post-to|ic-delete-from)="([^"]+)')


class Client(TestApp):
    skip_n_forms = False
    use_intercooler = False

    def spawn(self):
        """ Spawns a new client that points to the same app.

        All login data / cookies are lost.

        """

        return self.__class__(self.app)

    def login(self, username, password, to=None):
        """ Login a user through the usualy /auth/login path. """

        url = '/auth/login' + (to and ('/?to=' + to) or '')

        login_page = self.get(url)
        login_page.form.set('username', username)
        login_page.form.set('password', password)
        return login_page.form.submit()

    def login_admin(self, to=None):
        return self.login('admin@example.org', 'hunter2', to)

    def login_editor(self, to=None):
        return self.login('editor@example.org', 'hunter2', to)

    def login_member(self, to=None):
        return self.login('member@example.org', 'hunter2', to)

    def logout(self):
        return self.get('/auth/logout')

    def get_email(self, batch_index, index=0, flush_queue=False):
        """ Get the nth email from the batch at the given batch index.
        This will be dictionary formatted to suit the Postmark API

        :param flush_queue: Should the email queue be emptied after
            retrieving the email?

        See: https://postmarkapp.com/developer/api/email-api
        """
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

    def flush_email_queue(self):
        for path in os.listdir(self.app.maildir):
            os.remove(os.path.join(self.app.maildir, path))

    def extract_href(self, link):
        """ Takes a link (<a href...>) and returns the href address. """

        result = EXTRACT_HREF.search(link)
        return result and result.group(1) or None

    def extend_response(self, response):
        """ Takes the default response and adds additional methods/properties,
        or overrides them.

        """
        bases = [GenericResponseExtension]

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

        return response

    def do_request(self, *args, **kwargs):
        """ Dirtily inject extra methods into the response -> done this way
        because not all testclients support overriding the response class
        (i.e. webtest-selenium).

        """

        return self.extend_response(super().do_request(*args, **kwargs))


class GenericResponseExtension:

    def select_checkbox(self, groupname, label, form=None, checked=True):
        """ Selects one of many checkboxes by fuzzy searching the label next to
        it. Webtest is not good enough in this regard.

        Selects the checkbox from the form returned by page.form, or the given
        form if passed. In any case, the form needs to be part of the page.

        """

        elements = self.pyquery(f'input[name="{groupname}"]')

        if not elements:
            raise KeyError(f"No input named {groupname} found")

        form = form or self.form

        for ix, el in enumerate(elements):
            if label in el.label.text_content():
                form.get(groupname, index=ix).value = checked

    def select_radio(self, groupname, label, form=None):
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
    def pyquery(self):
        """ Webtests property of the same name seems to not work on all
        pages (it uses self.testbody and not self.body) and it also doesn't
        cache the result, which is an easy way to improve some lookups here.

        """
        return pq(self.body)

    def __or__(self, text):
        """ Grep style searching the response, e.g.
        `print(client.get('/') | 'Text')`

        """
        return '\n'.join([l for l in str(self).split('\n') if text in l])


class SkipNFormsExtension:
    n = 0

    @property
    def form(self):
        """ Use Form with ID 'main-form', else ignore the first n forms.

        """
        if 'main-form' in self.forms:
            return self.forms['main-form']

        if len(self.forms) > self.n:
            return self.forms[self.n]
        else:
            return super().form


class IntercoolerClickExtension:

    def click(self, description=None, linkid=None, href=None,
              index=None, verbose=False,
              extra_environ=None):
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

    def find_ic_url(self, description, linkid, href, index, verbose):

        attrs = (
            ('post', 'ic-post-to'),
            ('delete', 'ic-delete-from'),
            ('get', 'ic-get-from'),
        )

        for method, attr in attrs:
            url = self.find_ic_url_by_attr(
                attr=attr,
                content=description,
                href_extract=None,
                id=linkid,
                href_pattern=href,
                index=index,
                verbose=verbose)

            if url:
                return method, url

    def find_ic_url_by_attr(self, attr, **kwargs):
        try:
            html, desc, attrs = self._find_element(
                tag='a', href_attr=attr, **kwargs)

            return attrs[attr]
        except IndexError:
            return None
