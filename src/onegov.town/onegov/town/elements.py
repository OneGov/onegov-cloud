""" Contains small helper classes used as abstraction for various templating
macros.

"""

from lxml.html import builder, tostring
from onegov.town import _
from purl import URL


class HiddenElementMixin(object):

    @property
    def is_hidden_from_public(self):
        """ Returns True if Link is hidden from the public. Pass extra keyword
        ``model`` to ``__init__`` to have this work automatically.

        """
        if self.model and self.model.is_hidden_from_public:
            return True
        else:
            return False


class Link(HiddenElementMixin):
    """ Represents a link rendered in a template. """

    __slots__ = [
        'active',
        'attributes',
        'classes',
        'model',
        'request_method',
        'subtitle',
        'text',
        'url',
    ]

    def __init__(self, text, url, classes=None, request_method='GET',
                 attributes={}, active=False, model=None, subtitle=None):

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

        #: Indicate if this link is active or not (not used for rendering)
        self.active = active

        #: The model that underlies this link (to check if the link is visible)
        self.model = model

        #: Shown as a subtitle below certain links (not automatically rendered)
        self.subtitle = subtitle

    def __eq__(self, other):
        for attr in self.__slots__:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __call__(self, request, extra_classes=None):
        """ Renders the element. """

        a = builder.A(request.translate(self.text))

        if self.request_method == 'GET':
            a.attrib['href'] = self.url

        if self.request_method == 'POST':
            a.attrib['ic-post-to'] = self.url

        if self.request_method == 'DELETE':
            url = URL(self.url).query_param(
                'csrf-token', request.new_csrf_token())

            a.attrib['ic-delete-from'] = url.as_string()

        if self.classes or extra_classes:
            classes = self.classes + (extra_classes or tuple())
            a.attrib['class'] = ' '.join(classes)

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


class DeleteLink(Link):

    def __init__(self, text, url, confirm,
                 yes_button_text=None,
                 no_button_text=None,
                 extra_information=None,
                 redirect_after=None,
                 request_method='DELETE'):

        attr = {
            'data-confirm': confirm
        }

        if extra_information:
            attr['data-confirm-extra'] = extra_information

        if yes_button_text:
            attr['data-confirm-yes'] = yes_button_text

        if no_button_text:
            attr['data-confirm-no'] = no_button_text
        else:
            attr['data-confirm-no'] = _("Cancel")

        if redirect_after:
            attr['redirect-after'] = redirect_after

        if request_method == 'GET':
            attr['ic-get-from'] = url
            url = '#'

        super().__init__(
            text=text,
            url=url,
            classes=('confirm', 'delete-link'),
            request_method=request_method,
            attributes=attr
        )


class Img(object):
    """ Represents an img element. """

    __slots__ = ['src', 'alt', 'title', 'url']

    def __init__(self, src, alt=None, title=None, url=None):
        #: The src of the image
        self.src = src

        #: The text for people that can't or won't look at the picture
        self.alt = alt

        #: The title of the image
        self.title = title

        #: The target of this image
        self.url = url


class LinkGroup(HiddenElementMixin):
    """ Represents a list of links. """

    __slots__ = ['title', 'links', 'model', 'right_side']

    def __init__(self, title, links, model=None, right_side=True):
        self.title = title
        self.links = links
        self.model = model
        self.right_side = right_side
