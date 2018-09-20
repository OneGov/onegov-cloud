import html

from mistletoe import Document, HTMLRenderer
from onegov.core.html import sanitize_html


RENDERER_INSTANCES = {}


class HTMLRendererWithoutInlineHtml(HTMLRenderer):

    @staticmethod
    def render_html_block(token):
        return html.escape(token.content)

    @staticmethod
    def render_html_span(token):
        return html.escape(token.content)


def render_untrusted_markdown(markdown, cls=HTMLRendererWithoutInlineHtml):

    # use a global renderer instance, but only create it if used
    if cls not in RENDERER_INSTANCES:
        RENDERER_INSTANCES[cls] = cls()

    renderer = RENDERER_INSTANCES[cls]

    # mistletoe doesn't normalise line-endings, so we have to
    # see https://github.com/miyuchina/mistletoe/issues/64
    markdown = markdown.replace('\r\n', '\n')

    # render html
    html = renderer.render(Document(markdown))

    # clean it
    return sanitize_html(html)
