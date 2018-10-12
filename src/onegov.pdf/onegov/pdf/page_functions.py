from datetime import date
from textwrap import shorten
from textwrap import wrap


def empty_page_fn(cavnas, doc):
    """ An empty header/footer. """

    pass


def page_fn_footer(canvas, doc):
    """ A standard footer including the page numbers on the right and
    optionally a copyright with the author on the left.

    Example:

        pdf = Pdf(file, author='OneGov')
        pdf.init_a4_portrait(page_fn=draw_footer)

    """
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    if doc.author:
        canvas.drawString(
            doc.leftMargin,
            doc.bottomMargin / 2,
            '© {} {}'.format(date.today().year, doc.author)
        )
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        doc.bottomMargin / 2,
        f'{canvas._pageNumber}'
    )
    canvas.restoreState()


def page_fn_header(canvas, doc):
    """ A standard header consisting of a title and the creation string. The
    title is automatically wrapped and shortened.

    Example:

        pdf = Pdf(file, author='OneGov', crated='1.1.2000')
        pdf.init_a4_portrait(page_fn=draw_header)

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
    if doc.created:
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.pagesize[1] - doc.topMargin * 2 / 3,
            doc.created
        )
    canvas.restoreState()


def page_fn_header_and_footer(canvas, doc):
    """ A standard header and footer.

    Example:

        pdf = Pdf(file, title='Title', created='1.1.2000', author='OneGov')
        pdf.init_a4_portrait(
            page_fn=draw_footer,
            page_fn_later=draw_header_and_footer
        )

    """

    page_fn_header(canvas, doc)
    page_fn_footer(canvas, doc)
