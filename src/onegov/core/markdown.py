from __future__ import annotations

import html

from mistletoe import Document, HtmlRenderer
from onegov.core.html import sanitize_html


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from markupsafe import Markup
    from mistletoe.span_token import HTMLBlock, HTMLSpan  # type:ignore


RENDERER_INSTANCES = {}


class HTMLRendererWithoutInlineHtml(HtmlRenderer):

    @staticmethod
    def render_html_block(token: HTMLBlock) -> str:
        return html.escape(token.content)

    @staticmethod
    def render_html_span(token: HTMLSpan) -> str:
        return html.escape(token.content)


def render_untrusted_markdown(
    markdown: str,
    cls: type[HtmlRenderer] = HTMLRendererWithoutInlineHtml
) -> Markup:

    # use a global renderer instance, but only create it if used
    if cls not in RENDERER_INSTANCES:
        RENDERER_INSTANCES[cls] = cls()

    renderer = RENDERER_INSTANCES[cls]

    # mistletoe doesn't normalise line-endings, so we have to
    # see https://github.com/miyuchina/mistletoe/issues/64
    markdown = markdown.replace('\r\n', '\n')

    # render html
    html = renderer.render(Document(markdown))  # type:ignore[no-untyped-call]

    # clean it
    return sanitize_html(html)
