import pytest

from onegov.core.html import sanitize_html, sanitize_svg


def test_sanitize_html() -> None:
    # this is really bleach's job, but we want to run the codepath anyway
    assert sanitize_html('') == ''
    assert sanitize_html('<script>') == '&lt;script&gt;'
    assert sanitize_html('<b foo="x" foo:bar="y">') == '<b></b>'


def test_sanitize_html_link_classes() -> None:
    # call to action buttons keep their classes
    assert sanitize_html(
        '<a href="/forms" class="button cta secondary">Apply</a>'
    ) == '<a href="/forms" class="button cta secondary">Apply</a>'

    # other classes might trigger javascript behaviour, so they are removed
    assert sanitize_html(
        '<a href="/x" class="confirm delete-link button button">X</a>'
    ) == '<a href="/x" class="button">X</a>'
    assert sanitize_html(
        '<a href="/x" class="confirm">X</a>'
    ) == '<a href="/x">X</a>'

    # the classes don't make dangerous links safe
    assert sanitize_html(
        '<a href="javascript:alert(1)" class="button cta">X</a>'
    ) == '<a class="button cta">X</a>'


def test_sanitize_svg() -> None:
    with pytest.raises(AssertionError):
        assert sanitize_svg('<a xlink:href=”javascript:alert(9)”>')

    with pytest.raises(AssertionError):
        assert sanitize_svg('<a><![CDATA[ alert(); ]]></a>')

    with pytest.raises(AssertionError):
        assert sanitize_svg('<script>')

    with pytest.raises(AssertionError):
        assert sanitize_svg("<meta http-equiv='Set-Cookie' content='a=b' />")
