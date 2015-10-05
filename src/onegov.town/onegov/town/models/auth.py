from onegov.core.utils import relative_url


class Auth(object):

    def __init__(self, request, to=None):
        # never redirect to an external page, this might potentially be used
        # to trick the user into thinking he's on our page after entering his
        # password and being redirected to a phising site that looks like our
        # site.
        self.to = relative_url(to)
