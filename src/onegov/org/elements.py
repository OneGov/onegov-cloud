""" Contains small helper classes used as abstraction for various templating
macros.

"""
from __future__ import annotations

from random import choice

from lxml.html import builder, tostring
from markupsafe import Markup

from onegov.core.elements import AccessMixin, LinkGroup
from onegov.core.elements import Link as BaseLink
from onegov.org import _
from purl import URL


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterable
    from onegov.core.elements import Trait
    from onegov.core.elements import ChameleonLayout
    from onegov.core.request import CoreRequest

    # NOTE: We pretend to inherit from BaseLink at type checking time
    #       so we're not stuck in dependency hell everywhere else
    #       In reality we probably should actually inherit from this
    #       class and clean up redundancies...
    _Base = BaseLink
else:
    _Base = AccessMixin


class Link(_Base):
    """ Represents a link rendered in a template. """

    __slots__ = (
        'active',
        'attributes',
        'classes',
        'model',
        'request_method',
        'subtitle',
        'text',
        'url',
    )

    def __init__(
        self,
        text: str,
        url: str,
        classes: Collection[str] | None = None,
        request_method: str = 'GET',
        attributes: dict[str, Any] | None = None,
        active: bool = False,
        model: Any | None = None,
        subtitle: str | None = None
    ) -> None:

        #: The text of the link
        self.text: str = text

        #: The fully qualified url of the link
        self.url = url

        #: Classes included in the link
        self.classes = classes

        #: The link method, defaults to 'GET'. Also supported is 'DELETE',
        #: which will lead to the use of XHR
        self.request_method = request_method

        #: HTML attributes (may override other attributes set by this class).
        #: Attributes which are translatable, are transalted before rendering.
        self.attributes = attributes or {}

        #: Indicate if this link is active or not (not used for rendering)
        self.active = active

        #: The model that underlies this link (to check if the link is visible)
        self.model = model

        #: Shown as a subtitle below certain links (not automatically rendered)
        self.subtitle = subtitle

    def __eq__(self, other: object) -> bool:
        for attr in self.__slots__:
            if getattr(self, attr) != getattr(other, attr, None):
                return False
        return True

    def __call__(
        self,
        request: ChameleonLayout | CoreRequest,
        extra_classes: Iterable[str] | None = None
    ) -> Markup:
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

        classes: list[str] = []
        if self.classes:
            classes.extend(self.classes)
        if extra_classes:
            classes.extend(extra_classes)
        a.attrib['class'] = ' '.join(classes)

        # add the access hint if needed
        if self.access == 'private':

            # This snippet is duplicated in the access-hint macro!
            hint = builder.I()
            hint.attrib['class'] = 'private-hint'
            hint.attrib['title'] = request.translate(_('This site is private'))

            a.append(builder.I(' '))
            a.append(hint)

        elif self.access == 'secret':

            # This snippet is duplicated in the access-hint macro!
            hint = builder.I()
            hint.attrib['class'] = 'secret-hint'
            hint.attrib['title'] = request.translate(_('This site is secret'))

            a.append(builder.I(' '))
            a.append(hint)

        for key, value in self.attributes.items():
            a.attrib[key] = request.translate(value)

        return Markup(tostring(a, encoding=str))  # nosec: B704

    def __repr__(self) -> str:
        return f'<Link {self.text}>'


class QrCodeLink(BaseLink):
    """ Implements a qr code link that shows a modal with the QrCode.
    Thu url is sent to the qr endpoint url which generates the image
    and sends it back.
    """

    id = 'qr_code_link'

    __slots__ = (
        'active',
        'attributes',
        'classes',
        'text',
        'url',
        'title'
    )

    def __init__(
        self,
        text: str,
        url: str,
        title: str | None = None,
        attrs: dict[str, Any] | None = None,
        traits: Iterable[Trait] | Trait = (),
        **props: Any
    ) -> None:

        attrs = attrs or {}
        attrs['data-payload'] = url
        attrs['data-reveal-id'] = ''.join(
            choice('abcdefghi') for i in range(8)  # nosec B311
        )
        # Foundation 6 Compatibility
        attrs['data-open'] = attrs['data-reveal-id']
        attrs['data-image-parent'] = f"qr-{attrs['data-reveal-id']}"

        super().__init__(text, '#', attrs, traits, **props)
        self.title = title

    def __repr__(self) -> str:
        return f'<QrCodeLink {self.text}>'


class DeleteLink(Link):

    def __init__(
        self,
        text: str,
        url: str,
        confirm: str,
        yes_button_text: str | None = None,
        no_button_text: str | None = None,
        extra_information: str | None = None,
        redirect_after: str | None = None,
        request_method: str = 'DELETE',
        classes: Collection[str] = ('confirm', 'delete-link'),
        target: str | None = None,
        items: str | None = None,
        scroll_hint: str | None = None,
    ) -> None:

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
            attr['data-confirm-no'] = _('Cancel')

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

        if items:
            attr['data-confirm-items'] = items
            attr['data-scroll-hint'] = scroll_hint or ''

        super().__init__(
            text=text,
            url=url,
            classes=classes,
            request_method=request_method,
            attributes=attr
        )


class ConfirmLink(DeleteLink):
    # XXX this is some wonky class hierarchy with tons of parameters.
    # We can do better!

    def __init__(
        self,
        text: str,
        url: str,
        confirm: str,
        yes_button_text: str | None = None,
        no_button_text: str | None = None,
        extra_information: str | None = None,
        redirect_after: str | None = None,
        request_method: str = 'POST',
        classes: Collection[str] = ('confirm', )
    ) -> None:

        super().__init__(
            text, url, confirm, yes_button_text, no_button_text,
            extra_information, redirect_after, request_method, classes)


__all__ = (
    'AccessMixin',
    'ConfirmLink',
    'DeleteLink',
    'Link',
    'LinkGroup',
    'QrCodeLink'
)


class IFrameLink(BaseLink):
    """ Implements an iframe link that shows a modal with the iframe.
    The url is sent to the iframe endpoint url which generates the iframe
    and sends it back.
    """

    id = 'iframe_link'

    __slots__ = (
        'active',
        'attributes',
        'classes',
        'text',
        'url',
        'title'
    )

    def __init__(
        self,
        text: str,
        url: str,
        title: str | None = None,
        attrs: dict[str, Any] | None = None,
        traits: Iterable[Trait] | Trait = (),
        **props: Any
    ) -> None:

        attrs = attrs or {}
        attrs['new-iframe-link'] = (
            '<iframe src="'
            + url
            + '" width="100%" height="800" frameborder="0"></iframe>'
        )
        attrs['data-reveal-id'] = ''.join(
            choice('abcdefghi') for i in range(8)  # nosec B311
        )
        # Foundation 6 Compatibility
        attrs['data-open'] = attrs['data-reveal-id']
        attrs['data-image-parent'] = f"iframe-{attrs['data-reveal-id']}"

        super().__init__(text, '#', attrs, traits, **props)
        self.title = title

    def __repr__(self) -> str:
        return f'<IFrameLink {self.text}>'
