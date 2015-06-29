class HiddenMetaMixin(object):
    """ Extends any class with a meta dictionary field with the ability to
    hide it from the public.

    see :func:`onegov.core.security.rules.has_permission_not_logged_in`

    """

    @property
    def is_hidden_from_public(self):
        return self.meta.get('is_hidden_from_public', False)

    @is_hidden_from_public.setter
    def is_hidden_from_public(self, is_hidden):
        self.meta['is_hidden_from_public'] = is_hidden
