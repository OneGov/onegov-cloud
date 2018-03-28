import re

from webtest import TestApp


EXTRACT_HREF = re.compile(
    r'(?:href|ic-get-from|ic-post-to|ic-delete-from)="([^"]+)')


class Client(TestApp):
    skip_first_form = False
    use_intercooler = False

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

    def logout(self):
        return self.get('/auth/logout')

    def get_email(self, index, payload=0):
        """ Get the email at the given index, returning the nth payload (0 is
        usually text-only).

        """
        message = self.app.smtp.outbox[index]
        message = message.get_payload(payload).get_payload(decode=True)
        return message.decode('utf-8')

    def extract_href(self, link):
        """ Takes a link (<a href...>) and returns the href address. """

        result = EXTRACT_HREF.search(link)
        return result and result.group(1) or None

    def extend_response(self, response):
        """ Takes the default response and adds additional methods/properties,
        or overrides them.

        """
        bases = [GenericResponseExtension]

        if self.skip_first_form:
            bases.append(SkipFirstFormExtension)

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


class GenericResponseExtension(object):

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


class SkipFirstFormExtension(object):

    @property
    def form(self):
        """ Ignore the first form, which is the general search form on
        the top of the page.

        """
        if len(self.forms) > 1:
            return self.forms[1]
        else:
            return super().form


class IntercoolerClickExtension(object):

    def click(self, description=None, linkid=None, href=None,
              index=None, verbose=False,
              extra_environ=None):
        """ Adds intercooler.js support for links (by description). """
        try:
            return super().click(
                description, linkid, href, index, verbose, extra_environ)
        except IndexError:
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
                raise NotImplementedError

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
