from __future__ import annotations

from onegov.core.markdown import render_untrusted_markdown as render
from mistletoe import HtmlRenderer  # type: ignore[import-untyped]


def test_render_untrusted_markdown() -> None:

    # no unsafe html
    assert render("<table></table>") == '&lt;table&gt;&lt;/table&gt;\n'

    # this would usually result ina code class element, but we currently
    # do not allow classes to be set by untrusted html
    assert render('```python\nfoo\n```') == '<pre><code>foo\n</code></pre>\n'

    # inline html is disabled by default
    assert render('<a>foo</a>') == '<p>&lt;a&gt;foo&lt;/a&gt;</p>\n'

    # though we can enable it (it is still sanitized though)
    assert render('<a onclick="alert">foo</a>', cls=HtmlRenderer) == (
        '<p><a>foo</a></p>\n')


def test_markdown_line_endings() -> None:
    assert render('foo  \r\nbar') == render('foo  \nbar')
