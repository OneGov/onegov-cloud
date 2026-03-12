from __future__ import annotations

from onegov.core.utils import Bunch
from onegov.org import _
from onegov.core.elements import Link, Confirm, Intercooler


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import _RenderFunc


def test_link(render_element: _RenderFunc) -> None:
    # text is translated
    result = render_element(Link(text=_("Settings"), url='/settings'))
    assert result.pyquery('a').text() == "Einstellungen"
    assert result.pyquery('a').attr('href') == '/settings'

    # other attributes are rendered
    result = render_element(Link(text='foo', url='#', attrs={
        'data-foo': 'bar'
    }))
    assert result.pyquery('a').attr('data-foo') == 'bar'

    # we show a hint if the link is hidden from public
    result = render_element(Link(text='hidden', url='#', model=Bunch(
        access='private'
    )))

    assert result.pyquery('i').attr('title') == "Diese Seite ist privat"
    assert result.pyquery('i').attr('class') == 'private-hint'


def test_confirm_link(render_element: _RenderFunc) -> None:
    result = render_element(Link(text="Delete", url='#', traits=(
        Confirm(
            _("Login"),
            "Extra...",
            _("Yes"),
            _("No")
        ),
    ), attrs={'class': 'foo'}))

    assert result.pyquery('a').attr('data-confirm') == "Anmelden"
    assert result.pyquery('a').attr('data-confirm-extra') == "Extra..."
    assert result.pyquery('a').attr('data-confirm-yes') == "Ja"
    assert result.pyquery('a').attr('data-confirm-no') == "Nein"
    assert result.pyquery('a').attr('class') in ('foo confirm', 'confirm foo')


def test_link_slots() -> None:
    # make sure that the Link class as well as all its parents have
    # __slots__ defined (for some lookup speed and memory improvements)
    assert not hasattr(Link("Slots", '#'), '__dict__')


def test_intercooler_link(render_element: _RenderFunc) -> None:
    result = render_element(Link(text="Delete", traits=Intercooler(
        request_method="POST", redirect_after='#redirect', target='#target'
    )))

    assert result.pyquery('a').attr('ic-post-to') == '#'
    assert result.pyquery('a').attr('ic-target') == '#target'
    assert result.pyquery('a').attr('redirect-after') == '#redirect'
    assert result.pyquery('a').attr('href') is None


def test_class_attributes(render_element: _RenderFunc) -> None:
    result = render_element(Link(text="Delete", attrs={
        'class': 'foo'
    }))
    assert result.pyquery('a').attr('class') == 'foo'

    result = render_element(Link(text="Delete", attrs={
        'class': ('foo', 'bar')
    }))
    assert result.pyquery('a').attr('class') in ('foo bar', 'bar foo')

    result = render_element(Link(text="Delete", attrs={
        'class': ('foo', 'bar')
    }))
    assert result.pyquery('a').attr('class') in ('foo bar', 'bar foo')

    result = render_element(Link(text="Delete"))
    assert result.pyquery('a').attr('class') is None
