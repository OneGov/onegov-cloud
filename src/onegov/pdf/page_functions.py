from __future__ import annotations

from datetime import date
from lxml import etree
from textwrap import shorten
from textwrap import wrap


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pdf.templates import Template
    from reportlab.pdfgen.canvas import Canvas


def empty_page_fn(canvas: Canvas, doc: Template) -> None:
    """ An empty header/footer. """


def page_fn_footer(canvas: Canvas, doc: Template) -> None:
    """ A standard footer including the page numbers on the right and
    optionally a copyright with the author on the left.

    Example::

        pdf = Pdf(file, author='OneGov')
        pdf.init_a4_portrait(page_fn=page_fn_footer)

    """
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    if doc.author:
        canvas.drawString(
            doc.leftMargin,
            doc.bottomMargin / 2,
            f'© {date.today().year} {doc.author}'
        )
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        doc.bottomMargin / 2,
        f'{canvas.getPageNumber()}'
    )
    canvas.restoreState()


def page_fn_header(canvas: Canvas, doc: Template) -> None:
    """ A standard header consisting of a title and the creation string. The
    title is automatically wrapped and shortened.

    Example::

        pdf = Pdf(file, author='OneGov', created='1.1.2000')
        pdf.init_a4_portrait(page_fn=page_fn_header)

    """

    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    if doc.title:
        lines = wrap(doc.title, 110)[:2]
        if len(lines) > 1:
            lines[1] = shorten(lines[1], 100)
        text = canvas.beginText()
        text.setTextOrigin(
            doc.leftMargin,
            doc.pagesize[1] - doc.topMargin * 2 / 3
        )
        text.textLines(lines)
        canvas.drawText(text)
    if created := getattr(doc, 'created', None):
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.pagesize[1] - doc.topMargin * 2 / 3,
            created
        )
    canvas.restoreState()


def page_fn_header_logo(canvas: Canvas, doc: Template) -> None:
    """ A standard header consisting of a SVG logo.

    The logo is drawn in its original size placed at the bottom on the header,
    which allows to give extra margin at the bottom directly in the SVG.

    Example::

        pdf = Pdf(
            file, author='OneGov', created='1.1.2000',
            logo='<?xml version="1.0"><svg>...</svg>'
        )
        pdf.init_a4_portrait(page_fn=page_fn_header_logo)

    """

    # reportlab and svglib are particularly heavy imports which are loaded by
    # morepath's scan - until we can teach that scanner to ignore certain
    # modules automatically we lazy load these modules here
    from reportlab.graphics import renderPDF
    from svglib.svglib import SvgRenderer

    canvas.saveState()
    if logo := getattr(doc, 'logo', None):
        parser = etree.XMLParser(remove_comments=True, recover=True)
        svg = etree.fromstring(logo.encode('utf-8'), parser=parser)
        drawing = SvgRenderer(path=None).render(svg)  # type: ignore[arg-type]
        renderPDF.draw(
            drawing,
            canvas,
            doc.leftMargin,
            doc.pagesize[1] - doc.topMargin
        )
    canvas.restoreState()


def page_fn_header_and_footer(canvas: Canvas, doc: Template) -> None:
    """ A standard header and footer.

    Example::

        pdf = Pdf(file, title='Title', created='1.1.2000', author='OneGov')
        pdf.init_a4_portrait(
            page_fn=page_fn_footer,
            page_fn_later=page_fn_header_and_footer
        )

    """

    page_fn_header(canvas, doc)
    page_fn_footer(canvas, doc)


def page_fn_header_logo_and_footer(canvas: Canvas, doc: Template) -> None:
    """ A standard header logo and footer.

    Example::

        pdf = Pdf(
            file, title='Title', created='1.1.2000', author='OneGov',
            logo='<?xml version="1.0"><svg>...</svg>'
        )
        pdf.init_a4_portrait(
            page_fn=page_fn_header_logo_and_footer,
            page_fn_later=page_fn_header_and_footer
        )

    """

    page_fn_header_logo(canvas, doc)
    page_fn_footer(canvas, doc)
