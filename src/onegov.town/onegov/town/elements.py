""" Contains small helper classes used as abstraction for various templating
macros.

"""

from lxml.html import builder, tostring
from purl import URL


class Link(object):
    """ Represents a link rendered in a template. """

    def __init__(self, text, url, classes=None, request_method='GET',
                 attributes={}, **extra):

        #: The text of the link
        self.text = text

        #: The fully qualified url of the link
        self.url = url

        #: Classes included in the link
        self.classes = classes

        #: The link method, defaults to 'GET'. Also supported is 'DELETE',
        #: which will lead to the use of XHR
        self.request_method = request_method

        #: HTML attributes (may override other attributes set by this class).
        #: Attributes which are translatable, are transalted before rendering.
        self.attributes = attributes

        #: The extra dictionary is applied to the class
        for key, value in extra.items():
            setattr(self, key, value)

    def __call__(self, request):
        """ Renders the element. """

        a = builder.A(request.translate(self.text))

        if self.request_method == 'GET':
            a.attrib['href'] = self.url

        if self.request_method == 'DELETE':
            url = URL(self.url).query_param(
                'csrf-token', request.new_csrf_token())

            a.attrib['ic-delete-from'] = url.as_string()

        if self.classes:
            a.attrib['class'] = ' '.join(self.classes)

        for key, value in self.attributes.items():
            a.attrib[key] = request.translate(value)

        return tostring(a)


class Image(object):
    """ Represents an img element. """

    def __init__(self, src, alt=None, title=None):
        #: The src of the image
        self.src = src

        #: The text for people that can't or won't look at the picture
        self.alt = alt

        #: The title of the image
        self.title = title
