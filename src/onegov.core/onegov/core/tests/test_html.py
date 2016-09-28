import pytest

from onegov.core.html import sanitize_html, sanitize_svg


def test_sanitize_html():
    # this is really bleach's job, but we want to run the codepath anyway
    assert sanitize_html('') == ''
    assert sanitize_html('<script>') == '&lt;script&gt;'
    assert sanitize_html('<b foo="x" foo:bar="y">') == '<b></b>'


def test_sanitize_svg():
    with pytest.raises(AssertionError):
        assert sanitize_svg('<a xlink:href=”javascript:alert(9)”>')

    with pytest.raises(AssertionError):
        assert sanitize_svg('<a><![CDATA[ alert(); ]]></a>')

    with pytest.raises(AssertionError):
        assert sanitize_svg('<script>')
