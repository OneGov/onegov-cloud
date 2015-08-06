from cached_property import cached_property


class Clipboard(object):
    """ The clipboard holds a url that should be copied and then pasted.
    The url is expected to be stored in a token that has been created by
    :meth:`onegov.core.request.CoreRequest.new_url_safe_token`.

    The reason behind this is that the url is used to fetch the object behind
    the url in an unrestricted fashion.

    """

    def __init__(self, request, token):
        self.request = request
        self.token = token

    @cached_property
    def url(self):
        data = self.request.load_url_safe_token(self.token, salt='clipboard')
        return data and data['url'] or None

    def get_object(self):
        if not self.url:
            return None

        return self.request.app.object_by_path(self.url)

    def clear(self):
        if self.request.browser_session.has('clipboard_url'):
            del self.request.browser_session['clipboard_url']

    def store_in_session(self):
        if self.url:
            self.request.browser_session['clipboard_url'] = self.url

    @classmethod
    def from_url(cls, request, url):
        return cls(
            request,
            request.new_url_safe_token({'url': url}, salt='clipboard')
        )

    @classmethod
    def from_session(cls, request):
        return cls(
            request,
            request.new_url_safe_token(
                {'url': request.browser_session.get('clipboard_url')},
                salt='clipboard'
            )
        )
