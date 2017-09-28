""" Simple redirects for renamed paths using a generic redirect model.

For static paths::

    @App.path('/old-path')
    class OldPathRedirect(Redirect):
        to = '/new-path'

For wildcard paths (e.g. /old-pages/my-page to /new-pages/my-page)::

    @App.path('/old-path', absorb=True)
    class OldPagesRedirect(Redirect):
        to = '/new-pages

"""

from onegov.core import Framework
from onegov.core.security import Public


class Redirect(object):
    to = None

    def __init__(self, absorb=None):
        assert self.to and not self.to.endswith('/')

        if absorb:
            self.to = self.to + '/' + absorb


@Framework.view(model=Redirect, permission=Public)
def view_redirect(self, request):
    return request.redirect(self.to)
