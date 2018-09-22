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

from onegov.core.templates import render_macro
from onegov.org import _

# currently used for backwards compatibility, this should become a regular
# element as well
from onegov.org.elements import LinkGroup  # noqa


class Element(object):
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
    id = None

    __slots__ = ('text', 'attrs', 'props')

    def __init__(self, text=None, attrs=None, traits=(), **props):
        self.text = text
        self.props = props
        self.attrs = self.normalize_attrs(attrs)

        if isinstance(traits, Trait):
            traits = (traits, )

        for trait in traits:
            self.attrs = trait(self.attrs, **props)

    def normalize_attrs(self, attrs):
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

    def __eq__(self, other):
        return self.id == other.id\
            and self.attrs == other.attrs\
            and self.props == other.props

    def __getattr__(self, name):
        if name in self.props:
            return self.props[name]

        raise AttributeError(name)

    def __call__(self, layout, extra_classes=None):
        if extra_classes:
            self.attrs['class'].update(extra_classes)

        if self.attrs['class']:
            if not isinstance(self.attrs['class'], str):
                self.attrs['class'] = ' '.join(self.attrs['class'])
        else:
            del self.attrs['class']

        return render_macro(layout.elements[self.id], layout.request, {
            'e': self, 'layout': layout,
        })


class HiddenLinkMixin(object):
    """ Hidden links point to views which are not available to the public
    (usually through a publication mechanism).

    We mark those links with an icon. This mixin automatically does that
    for links which bear a model property.

    """

    __slots__ = ()

    @property
    def is_hidden_from_public(self):
        """ Returns True if Link is hidden from the public. Pass extra keyword
        ``model`` to ``__init__`` to have this work automatically.

        """
        if hasattr(self, 'model'):
            return getattr(self.model, 'is_hidden_from_public', False)

        return False


class Link(Element, HiddenLinkMixin):
    """ A generic link. """

    id = 'link'

    __slots__ = ()

    def __init__(self, text, url='#', attrs=None, traits=(), **props):
        # this is the only exception we permit where we don't use a trait
        # to change the attributes - we do this because the url is essential
        # to a link, so it makes sense to have it as a proper argument
        attrs = attrs or {}
        attrs['href'] = url

        super().__init__(text, attrs, traits, **props)


class Trait(object):
    """ Base class for all traits. """

    __slots__ = ('apply', )

    def __call__(self, attrs, **ignored):
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

    def __init__(self, confirm, extra=None, yes=_("Yes"), no=_("Cancel"),
                 **ignored):
        def apply(attrs):
            attrs['class'].add('confirm')
            attrs['data-confirm'] = confirm
            attrs['data-confirm-extra'] = extra
            attrs['data-confirm-yes'] = yes
            attrs['data-confirm-no'] = no
            return attrs

        self.apply = apply


class Block(Confirm):
    """ A block trait is a confirm variation with no way to say yes. """

    __slots__ = ()

    def __init__(self, message, extra=None, **ignored):
        super().__init__(message, extra, yes=None)


class Intercooler(Trait):
    """ Turns the link into an intercooler request. As a result, the link
    will be exeucted as an ajax request.

    See http://intercoolerjs.org.
    """

    __slots__ = ()

    def __init__(self, request_method, target=None, redirect_after=None,
                 **ignored):
        def apply(attrs):
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
