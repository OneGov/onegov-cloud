from dogpile.cache.api import NO_VALUE


class BrowserSession(object):
    """ A session bound to a token (session_id cookie). Used to store data
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

    def __init__(self, namespace, token, cache, on_dirty=None):
        self._namespace = namespace
        self._token = token
        self._cache = cache
        self._on_dirty = on_dirty or self._on_dirty
        self._is_dirty = False

    def _on_dirty(self, namespace, token):
        """ Called when the browser session gets dirty. That is, the first time
        a change is made to the cache.

        Use ``on_dirty`` in the :meth:`__init__` method to override.

        """
        pass

    def mangle(self, name):
        """ Takes the given name and returns a key bound to the namespace and
        token.

        """
        assert name  # may not be empty or None
        return ':'.join((self._namespace, self._token, name))

    def has(self, name):
        """ Returns true if the given name exists in the cache. """
        return self._cache.get(self.mangle(name)) is not NO_VALUE

    def get(self, name, default=None):
        value = self._cache.get(self.mangle(name))

        if value is NO_VALUE:
            return default
        else:
            return value

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

            if not self._is_dirty:
                self._on_dirty(self._namespace, self._token)

            self._is_dirty = True

    def __delattr__(self, name):
        if name.startswith('_'):
            super(BrowserSession, self).__delattr__(name)
        else:
            self._cache.delete(self.mangle(name))

            if not self._is_dirty:
                self._on_dirty(self._namespace, self._token)

            self._is_dirty = True

    # act like a dict
    def __getitem__(self, name, *args):
        result = self._cache.get(self.mangle(name))

        if result is NO_VALUE:
            raise KeyError
        else:
            return result

    __setitem__ = __setattr__
    __delitem__ = __delattr__
    __delattr__ = __delattr__
    __contains__ = has
