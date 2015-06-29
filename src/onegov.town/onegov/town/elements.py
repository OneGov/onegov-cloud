""" Contains small helper classes used as abstraction for various templating
macros.

"""

from lxml.html import builder, tostring
from onegov.town import _
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

    @property
    def is_hidden_from_public(self):
        """ Returns True if Link is hidden from the public. Pass extra keyword
        ``model`` to ``__init__`` to have this work automatically.

        """
        if hasattr(self, 'model') and self.model.is_hidden_from_public:
            return True
        else:
            return False

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

        # add the hidden from public hint if needed
        if self.is_hidden_from_public:

            # This snippet is duplicated in the hidden-from-public-hint macro!
            hint = builder.I()
            hint.attrib['class'] = 'hidden-from-public-hint'
            hint.attrib['title'] = request.translate(
                _("This site is hidden from the general public")
            )

            a.append(builder.I(' '))
            a.append(hint)

        for key, value in self.attributes.items():
            a.attrib[key] = request.translate(value)

        return tostring(a)


class Img(object):
    """ Represents an img element. """

    def __init__(self, src, alt=None, title=None, url=None):
        #: The src of the image
        self.src = src

        #: The text for people that can't or won't look at the picture
        self.alt = alt

        #: The title of the image
        self.title = title

        #: The target of this image
        self.url = url


class LinkGroup(object):
    """ Represents a list of links. """

    def __init__(self, title, links):
        self.title = title
        self.links = links
