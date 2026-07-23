from __future__ import annotations

import pytest

from onegov.core.html import sanitize_html, sanitize_svg


def test_sanitize_html() -> None:
    # this is really bleach's job, but we want to run the codepath anyway
    assert sanitize_html('') == ''
    assert sanitize_html('<script>') == '&lt;script&gt;'
    assert sanitize_html('<b foo="x" foo:bar="y">') == '<b></b>'
    assert sanitize_html(
        '<details open><summary><h2>Toggle</h2></summary>'
        '<p>Content</p></details>'
    ) == (
        '<details><summary><h2>Toggle</h2></summary>'
        '<p>Content</p></details>'
    )
    assert sanitize_html(
        '<figure><img src="/image.jpg" alt="Image">'
        '<figcaption>Caption</figcaption></figure>'
    ) == (
        '<figure><img src="/image.jpg" alt="Image">'
        '<figcaption>Caption</figcaption></figure>'
    )
    assert sanitize_html(
        '<table><colgroup><col style="width: 120px"><col><col></colgroup>'
        '<tbody><tr><td>One</td><td>Two</td><td>Three</td></tr>'
        '</tbody></table>'
    ) == (
        '<table><colgroup><col><col><col></colgroup>'
        '<tbody><tr><td>One</td><td>Two</td><td>Three</td></tr>'
        '</tbody></table>'
    )


def test_sanitize_svg() -> None:
    with pytest.raises(AssertionError):
        assert sanitize_svg('<a xlink:href=”javascript:alert(9)”>')

    with pytest.raises(AssertionError):
        assert sanitize_svg('<a><![CDATA[ alert(); ]]></a>')

    with pytest.raises(AssertionError):
        assert sanitize_svg('<script>')

    with pytest.raises(AssertionError):
        assert sanitize_svg("<meta http-equiv='Set-Cookie' content='a=b' />")
