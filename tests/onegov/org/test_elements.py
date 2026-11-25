from __future__ import annotations

import pytest

from onegov.org.elements import (
    ConfirmLink,
    DeleteLink,
    IFrameLink,
    Link,
    QrCodeLink,
)


def test_link_equality_and_repr() -> None:
    link = Link('Home', '/home')
    assert link == Link('Home', '/home')
    assert link != Link('Home', '/other')
    assert link != object()
    assert repr(link) == '<Link Home>'


def test_qr_code_link() -> None:
    link = QrCodeLink('QR', 'https://example.org', title='Title')
    assert link.title == 'Title'
    assert repr(link) == '<QrCodeLink QR>'


def test_iframe_link() -> None:
    link = IFrameLink('Frame', 'https://example.org')
    assert repr(link) == '<IFrameLink Frame>'


def test_delete_link_methods() -> None:
    # DELETE keeps the url and sets the confirm attributes
    delete = DeleteLink(
        'Delete', '/entry', confirm='Sure?',
        extra_information='info', yes_button_text='Yes')
    assert delete.url == '/entry'
    assert delete.attributes['data-confirm'] == 'Sure?'
    assert delete.attributes['data-confirm-extra'] == 'info'
    assert delete.attributes['data-confirm-yes'] == 'Yes'

    # GET rewrites the url to '#' and uses ic-get-from
    get = DeleteLink('Delete', '/entry', confirm='S', request_method='GET')
    assert get.url == '#'
    assert get.attributes['ic-get-from'] == '/entry'

    # POST uses ic-post-to
    post = DeleteLink('Delete', '/entry', confirm='S', request_method='POST')
    assert post.attributes['ic-post-to'] == '/entry'

    # items set the confirm-items attribute
    with_items = DeleteLink(
        'Delete', '/entry', confirm='S', items='3', scroll_hint='hint')
    assert with_items.attributes['data-confirm-items'] == '3'

    # an unsupported method raises
    with pytest.raises(NotImplementedError):
        DeleteLink('Delete', '/entry', confirm='S', request_method='PUT')


def test_confirm_link() -> None:
    link = ConfirmLink('Confirm', '/entry', confirm='Sure?')
    assert link.attributes['data-confirm'] == 'Sure?'
