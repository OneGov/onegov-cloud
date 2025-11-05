""" Elements are mini chameleon macros, usually used to render a single
element. Sometimes it is useful to not just apply a macro, but to have an
actual object representing that code snippet. The prime example being links.

Elements are rendered in chameleon templates by calling them with the layout
object::

    <tal:b replace="structure element(layout)" />

Note that no matter how quick the elements rendering is, using chameleon
templates directly is faster.

This module should eventually replace the elements.py module.

"""
from __future__ import annotations

from onegov.core.templates import render_macro


from typing import Any, ClassVar, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Sequence
    from markupsafe import Markup

    from .layout import ChameleonLayout


class Element:
    """ Provides a way to define elements trough multiple variables. These
    elements may then be rendered by the elements.pt templates.

    Elements are simple, they render whatever text and attributes the get.
    They also carry a dictionary with properties on them, so any kind of
    value may be attached to an element. For example this works::

        user = object()
        element = Element(model=user)
        assert element.user == user

    Since we might use a complex set of attributes which need to be set in
    a certain way we use a traits system to avoid having to rely too heavily
    on class inheritance.

    Basically traits are callables called with attributes which they may
    manipulate. For example, a trait might turn a simple argument into
    a set of attributes::

        Element(traits=[Editor(buttons=['new', 'edit', 'delete'])])

    See the link traits further down to see examples.

    """

    # The link refers to the id of the macro written in elements.pt
    id: ClassVar[str | None] = None

    __slots__ = ('text', 'attrs', 'props')

    def __init__(
        self,
        text: str | None = None,
        attrs: dict[str, Any] | None = None,
        traits: Iterable[Trait] | Trait = (),
        **props: Any
    ):
        self.text = text
        self.props = props
        self.attrs = self.normalize_attrs(attrs)

        if isinstance(traits, Trait):
            traits = (traits, )

        for trait in traits:
            self.attrs = trait(self.attrs, **props)

    def normalize_attrs(self, attrs: dict[str, Any] | None) -> dict[str, Any]:
        """ Before we do anything with attributes we make sure we can easily
        add/remove classes from them, so we use a set.

        """
        attrs = attrs or {}

        if 'class' not in attrs:
            attrs['class'] = set()
        elif isinstance(attrs['class'], str):
            attrs['class'] = set(attrs['class'].split(' '))
        else:
            attrs['class'] = set(attrs['class'])

        return attrs

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Element)
            and self.id == other.id
            and self.attrs == other.attrs
            and self.props == other.props)

    def __getattr__(self, name: str) -> Any:
        # Handle special attributes that deepcopy looks for
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        if name in self.props:
            return self.props[name]
        raise AttributeError(name)

    def __call__(
        self,
        layout: ChameleonLayout,
        extra_classes: Iterable[str] | None = None
    ) -> Markup:

        assert self.id is not None

        if extra_classes:
            self.attrs['class'].update(extra_classes)

        if self.attrs['class']:
            if not isinstance(self.attrs['class'], str):
                self.attrs['class'] = ' '.join(self.attrs['class'])
        else:
            del self.attrs['class']

        return render_macro(
            layout.elements[self.id],
            layout.request,
            {'e': self, 'layout': layout}
        )


class AccessMixin:
    """ Hidden links point to views which are not available to the public
    (usually through a publication mechanism).

    We mark those links with an icon. This mixin automatically does that
    for links which bear a model property.

    """

    __slots__ = ()

    @property
    def access(self) -> str:
        """ Wraps model.access, ensuring it is always available, even if the
        model does not use it.

        """
        if hasattr(self, 'model'):
            return getattr(self.model, 'access', 'public')

        return 'public'


class Link(Element, AccessMixin):
    """ A generic link. """

    id = 'link'

    __slots__ = ()

    def __init__(
        self,
        text: str | None,
        url: str = '#',
        attrs: dict[str, Any] | None = None,
        traits: Iterable[Trait] | Trait = (),
        **props: Any
    ):
        # this is the only exception we permit where we don't use a trait
        # to change the attributes - we do this because the url is essential
        # to a link, so it makes sense to have it as a proper argument
        attrs = attrs or {}
        attrs['href'] = url

        super().__init__(text, attrs, traits, **props)

    def __repr__(self) -> str:
        return f'<Link {self.text}>'


class Button(Link):
    """ A generic button. """

    id = 'button'

    __slots__ = ()

    def __repr__(self) -> str:
        return f'<Button {self.text}>'


class BackLink(Link):
    """ A button that goes back in the history. """

    id = 'back_link'

    __slots__ = ()

    def __init__(
        self,
        text: str = '',
        **props: Any
    ):
        super().__init__(text, **props)

    def __repr__(self) -> str:
        return f'<BackButton {self.text}>'


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

    def __init__(
        self,
        title: str,
        links: Sequence[Link],
        model: Any | None = None,
        right_side: bool = True,
        classes: Collection[str] | None = None,
        attributes: dict[str, Any] | None = None
    ):
        self.title = title
        self.links = links
        self.model = model
        self.right_side = right_side
        self.classes = classes
        self.attributes = attributes


class Trait:
    """ Base class for all traits. """

    __slots__ = ('apply', )

    apply: Callable[[dict[str, Any]], dict[str, Any]]

    def __call__(
        self,
        attrs: dict[str, Any],
        **ignored: Any
    ) -> dict[str, Any]:
        return self.apply(attrs)


class Confirm(Trait):
    """ Links with a confirm link will only be triggered after a question has
    been answered with a yes::

        link = Link(_("Continue"), '/last-step', traits=(
            Confirm(
                _("Do you really want to continue?"),
                _("This cannot be undone"),
                _("Yes"), _("No")
            ),
        ))

    """

    __slots__ = ()

    def __init__(
        self,
        confirm: str,
        extra: str | None = None,
        yes: str | None = 'Yes',
        no: str = 'Cancel',
        items: Sequence[str] | None = None,
        scroll_hint: str | None = None,
        **ignored: Any
    ):
        def apply(attrs: dict[str, Any]) -> dict[str, Any]:
            attrs['class'].add('confirm')
            attrs['data-confirm'] = confirm
            attrs['data-confirm-extra'] = extra
            attrs['data-confirm-yes'] = yes
            attrs['data-confirm-no'] = no
            if items:
                attrs['data-confirm-items'] = items
                attrs['data-scroll-hint'] = scroll_hint
            return attrs

        self.apply = apply


class Block(Confirm):
    """ A block trait is a confirm variation with no way to say yes. """

    __slots__ = ()

    def __init__(
        self,
        message: str,
        extra: str | None = None,
        no: str = 'Cancel',
        **ignored: Any
    ):
        super().__init__(message, extra, None, no)


class Intercooler(Trait):
    """ Turns the link into an intercooler request. As a result, the link
    will be exeucted as an ajax request.

    See http://intercoolerjs.org.
    """

    __slots__ = ()

    def __init__(
        self,
        request_method: Literal['GET', 'POST', 'DELETE'],
        target: str | None = None,
        redirect_after: str | None = None,
        **ignored: Any
    ):
        def apply(attrs: dict[str, Any]) -> dict[str, Any]:
            if request_method == 'GET':
                attrs['ic-get-from'] = attrs['href']
            elif request_method == 'POST':
                attrs['ic-post-to'] = attrs['href']
            elif request_method == 'DELETE':
                attrs['ic-delete-from'] = attrs['href']

            del attrs['href']
            attrs['ic-target'] = target

            if redirect_after:
                attrs['redirect-after'] = redirect_after

            return attrs

        self.apply = apply
