""" Contains small helper classes used as abstraction for various templating
macros.

"""

from lxml.html import builder, tostring
from onegov.org import _
from purl import URL


class AccessMixin(object):

    @property
    def access(self):
        """ Wraps access to the model's access property, ensuring it always
        works, even if the model does not use it.

        """
        if hasattr(self, 'model'):
            return getattr(self.model, 'access', 'public')

        return 'public'


class Link(AccessMixin):
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

        # compatibility shim for new elements
        if hasattr(request, 'request'):
            request = request.request

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

        # add the access hint if needed
        if self.access == 'private':

            # This snippet is duplicated in the access-hint macro!
            hint = builder.I()
            hint.attrib['class'] = 'private-hint'
            hint.attrib['title'] = request.translate(_("This site is private"))

            a.append(builder.I(' '))
            a.append(hint)

        elif self.access == 'secret':

            # This snippet is duplicated in the access-hint macro!
            hint = builder.I()
            hint.attrib['class'] = 'secret-hint'
            hint.attrib['title'] = request.translate(_("This site is secret"))

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
                 request_method='DELETE',
                 classes=('confirm', 'delete-link'),
                 target=None):

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

        if target:
            attr['ic-target'] = target

        if request_method == 'GET':
            attr['ic-get-from'] = url
            url = '#'
        elif request_method == 'POST':
            attr['ic-post-to'] = url
            url = '#'
        elif request_method == 'DELETE':
            pass
        else:
            raise NotImplementedError

        super().__init__(
            text=text,
            url=url,
            classes=classes,
            request_method=request_method,
            attributes=attr
        )


class ConfirmLink(DeleteLink):
    # XXX this is some wonky class hierarchy with tons of paramters.
    # We can do better!

    def __init__(self, text, url, confirm,
                 yes_button_text=None,
                 no_button_text=None,
                 extra_information=None,
                 redirect_after=None,
                 request_method='POST',
                 classes=('confirm', )):

        super().__init__(
            text, url, confirm, yes_button_text, no_button_text,
            extra_information, redirect_after, request_method, classes)


class LinkGroup(AccessMixin):
    """ Represents a list of links. """

    __slots__ = [
        'title',
        'links',
        'model',
        'right_side',
        'classes',
        'attributes'
    ]

    def __init__(self, title, links,
                 model=None, right_side=True, classes=None, attributes=None):
        self.title = title
        self.links = links
        self.model = model
        self.right_side = right_side
        self.classes = classes
        self.attributes = attributes
