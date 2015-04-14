from dogpile.cache.api import NO_VALUE


class BrowserSession(object):
    """ A session bound to a token (sessionid cookie). Used to store data
    about a client on the server.

    Instances should be called ``browser_session`` to make sure we don't
    confuse this with the orm sessions.

    Used by :class:`onegov.core.request.CoreRequest`.

    Example:

        browser_session = request.browser_session
        browser_session.name = 'Foo'
        assert client.session.name == 'Foo'
        del client.session.name

    This class can act like an object, through attribute access, or like a
    dict, through square brackets. Whatever you prefer.

    """

    def __init__(self, namespace, token, cache):
        self._namespace = namespace
        self._token = token
        self._cache = cache

    def mangle(self, name):
        """ Takes the given name and returns a key bound to the namespace and
        token.

        """
        assert name  # may not be empty or None
        return ':'.join((self._namespace, self._token, name))

    def has(self, name):
        """ Returns true if the given name exists in the cache. """
        return self._cache.get(self.mangle(name)) is not NO_VALUE

    def __getattr__(self, name):
        result = self._cache.get(self.mangle(name))

        if result is NO_VALUE:
            raise AttributeError
        else:
            return result

    def __setattr__(self, name, value):
        if name.startswith('_'):
            super(BrowserSession, self).__setattr__(name, value)
        else:
            self._cache.set(self.mangle(name), value)

    def __delattr__(self, name):
        if name.startswith('_'):
            super(BrowserSession, self).__delattr__(name)
        else:
            self._cache.delete(self.mangle(name))

    # act like a dict
    def __getitem__(self, name):
        result = self._cache.get(self.mangle(name))

        if result is NO_VALUE:
            raise KeyError
        else:
            return result

    __setitem__ = __setattr__
    __delattr__ = __delattr__
    __contains__ = has
