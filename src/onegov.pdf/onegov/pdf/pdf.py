from bleach.sanitizer import Cleaner
from copy import deepcopy
from datetime import date
from html5lib.filters.whitespace import Filter as whitespace_filter
from io import StringIO
from lxml import etree
from onegov.pdf.flowables import InlinePDF
from pdfdocument.document import Empty
from pdfdocument.document import MarkupParagraph
from pdfdocument.document import PDFDocument
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.units import cm
from reportlab.platypus import Frame
from reportlab.platypus import ListFlowable
from reportlab.platypus import NextPageTemplate
from reportlab.platypus import PageTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Table
from textwrap import shorten
from textwrap import wrap


def empty_page_fn(cavnas, doc):
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
        '{}'.format(canvas._pageNumber)
    )
    canvas.restoreState()


def page_fn_header(canvas, doc):
    """ A standard header consisting of a title. The title is automatically
    wrapped and shortened.

    Example:

        pdf = Pdf(file, author='OneGov')
        pdf.init_a4_portrait(page_fn=draw_header)

    """

    if doc.title:
        canvas.saveState()
        lines = wrap(doc.title, 110)[:2]
        if len(lines) > 1:
            lines[1] = shorten(lines[1], 100)
        text = canvas.beginText()
        text.setFont('Helvetica', 9)
        text.setTextOrigin(
            doc.leftMargin,
            doc.pagesize[1] - doc.topMargin * 2 / 3
        )
        text.textLines(lines)
        canvas.drawText(text)
        canvas.restoreState()


def page_fn_header_and_footer(canvas, doc):
    """ A standard header and footer.

    Example:

        pdf = Pdf(file, author='OneGov')
        pdf.init_a4_portrait(
            page_fn=draw_footer,
            page_fn_later=draw_header_and_footer
        )

    """

    page_fn_header(canvas, doc)
    page_fn_footer(canvas, doc)


class Pdf(PDFDocument):
    """ A PDF document. """

    def __init__(self, *args, **kwargs):
        header_lines = kwargs.pop('header_lines', None)
        super(Pdf, self).__init__(*args, **kwargs)
        self.header_lines = header_lines

    def init_a4_portrait(self, page_fn=empty_page_fn, page_fn_later=None):
        frame_kwargs = {
            'showBoundary': self.show_boundaries,
            'leftPadding': 0,
            'rightPadding': 0,
            'topPadding': 0,
            'bottomPadding': 0,
        }

        width = 21 * cm
        height = 29.7 * cm
        margin_left = 2.5 * cm
        margin_right = 2.5 * cm
        margin_top = 3 * cm
        margin_bottom = 3 * cm

        full_frame = Frame(
            margin_left,
            margin_top,
            width - margin_left - margin_right,
            height - margin_top - margin_bottom,
            **frame_kwargs
        )

        self.doc.addPageTemplates([
            PageTemplate(
                id='First',
                frames=[full_frame],
                onPage=page_fn),
            PageTemplate(
                id='Later',
                frames=[full_frame],
                onPage=page_fn_later or page_fn),
        ])
        self.story.append(NextPageTemplate('Later'))

        self.generate_style(font_size=10)
        self.adjust_style(font_size=10)

    def adjust_style(self, font_size=10):
        """ Sets basic styling (borrowed from common browser defaults). """

        self.generate_style(font_size=font_size)

        self.style.heading1.fontSize = 2 * self.style.fontSize
        self.style.heading1.spaceBefore = 0.67 * self.style.heading1.fontSize
        self.style.heading1.spaceAfter = 0.67 * self.style.heading1.fontSize
        self.style.heading1.fontName = self.style.fontName
        self.style.heading1.textColor = self.style.normal.textColor
        self.style.heading1.leading = 1.2 * self.style.heading1.fontSize

        self.style.heading2.fontSize = 1.5 * self.style.fontSize
        self.style.heading2.spaceBefore = 0.83 * self.style.heading2.fontSize
        self.style.heading2.spaceAfter = 0.83 * self.style.heading2.fontSize
        self.style.heading2.fontName = self.style.fontName
        self.style.heading2.textColor = self.style.normal.textColor
        self.style.heading2.leading = 1.2 * self.style.heading2.fontSize

        self.style.heading3.fontSize = 1.17 * self.style.fontSize
        self.style.heading3.spaceBefore = 1 * self.style.heading3.fontSize
        self.style.heading3.spaceAfter = 1 * self.style.heading3.fontSize
        self.style.heading3.fontName = self.style.fontName
        self.style.heading3.textColor = self.style.normal.textColor
        self.style.heading3.leading = 1.2 * self.style.heading3.fontSize

        self.style.heading4 = deepcopy(self.style.normal)
        self.style.heading4.fontSize = 1 * self.style.fontSize
        self.style.heading4.spaceBefore = 1.33 * self.style.heading4.fontSize
        self.style.heading4.spaceAfter = 1.33 * self.style.heading4.fontSize
        self.style.heading4.fontName = self.style.fontName
        self.style.heading4.textColor = self.style.normal.textColor
        self.style.heading4.leading = 1.2 * self.style.heading4.fontSize

        self.style.paragraph.spaceAfter = 2 * self.style.paragraph.fontSize
        self.style.paragraph.leading = 1.2 * self.style.paragraph.fontSize

        self.style.ol = Empty()
        self.style.ol.bullet = '1'
        self.style.ol.leftIndent = 0
        self.style.ol.liIndent = 18  # from start of bullet to start of li

        self.style.ul = Empty()
        self.style.ul.bullet = 'bulletchar'
        self.style.ul.leftIndent = 0
        self.style.ul.liIndent = 18  # from start of bullet to start of li

        self.style.li = deepcopy(self.style.normal)
        self.style.li.leading = 1.2 * self.style.li.fontSize

        self.style.figcaption = deepcopy(self.style.paragraph)
        self.style.figcaption.fontSize = 0.85 * self.style.figcaption.fontSize
        self.style.figcaption.leftIndent = 2 * self.style.figcaption.fontSize
        self.style.figcaption.rightIndent = 2 * self.style.figcaption.fontSize

        self.style.table = (
            ('FONT', (0, 0), (-1, -1), self.style.fontName,
             self.style.fontSize),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('FIRSTLINEINDENT', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        )

        self.style.tableHead = (
            ('FONT', (0, 0), (-1, -1), self.style.fontName,
             self.style.fontSize),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('FIRSTLINEINDENT', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
            ('VALIGN', (1, 1), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.2, colors.black),
        )

    def h4(self, text, style=None):
        self.story.append(Paragraph(text, style or self.style.heading4))

    def fit_size(self, width, height, factor=1.0):
        """ Returns the given width and height so that it fits on the page. """

        doc_width = self.doc.width
        doc_height = self.doc.height * 0.9  # we cannot use the full height
        image_ratio = width / height
        page_ratio = doc_width / doc_height

        if page_ratio > image_ratio:
            return (
                factor * width * doc_height / height,
                factor * doc_height
            )
        else:
            return (
                factor * doc_width,
                factor * height * doc_width / width
            )

    def pdf(self, filelike, factor=1.0):
        """ Adds a PDF and fit it to the page. """

        img = InlinePDF(filelike, self.doc.width)
        if img.width and img.height:
            old = img.width
            img.width, img.height = self.fit_size(
                img.width, img.height, factor
            )
            img.scale = img.scale * img.width / old

            self.story.append(img)

    def table(self, data, columns, style=None, ratios=False):
        """ Adds a table where every cell is wrapped in a paragraph so that
        the cells are wrappable.

        """

        if columns == 'even':
            columns = None
            if len(data):
                rows = len(data[0])
                if rows:
                    columns = [self.doc.width / rows] * rows

        if ratios and columns:
            columns = [self.doc.width * p / sum(columns) for p in columns]

        data = [
            [
                cell if isinstance(cell, Paragraph) else
                MarkupParagraph(cell, deepcopy(self.style.normal))
                for cell in row
            ]
            for row in data
        ]

        # Copy the alignments from the table to the paragraphs
        def adjust(value):
            if value == -1:
                return None
            if value < 0:
                return value + 1
            return value

        alignments = {
            'CENTER': TA_CENTER,
            'LEFT': TA_LEFT,
            'RIGHT': TA_RIGHT,
        }

        style = style or self.style.table
        for st in style:
            if st[0] in ('ALIGN', 'ALIGNMENT'):
                for row in data[adjust(st[1][1]):adjust(st[2][1])]:
                    for cell in row[adjust(st[1][0]):adjust(st[2][0])]:
                        cell.style.alignment = alignments.get(st[3], TA_CENTER)

        self.story.append(Table(data, columns, style=style))

    def figcaption(self, text, style=None):
        """ Adds a figure caption. """

        self.p(text, style=style or self.style.figcaption)

    def mini_html(self, html):
        """ Convert a small subset of HTML into ReportLab paragraphs.

        This is very limited and currently supports only paragraphs and
        non-nested ordered/unordered lists.

        """

        if not html:
            return

        def strip(text):
            text = text.strip('\r\n')
            prefix = ' ' if text.startswith(' ') else ''
            postfix = ' ' if text.endswith(' ') else ''
            return prefix + text.strip() + postfix

        # Remove unwanted markup
        cleaner = Cleaner(
            tags=('p', 'br', 'strong', 'b', 'em', 'li', 'ol', 'ul', 'li'),
            attributes={},
            strip=True,
            filters=[whitespace_filter]
        )
        html = cleaner.clean(html or '')

        def inner_html(element):
            return '{}{}{}'.format(
                strip(element.text or ''),
                ''.join((
                    strip(etree.tostring(child, encoding='unicode'))
                    for child in element
                )),
                strip(element.tail or '')
            )

        # Walk the tree
        tree = etree.parse(StringIO(html), etree.HTMLParser())
        for element in tree.find('body'):
            if element.tag == 'p':
                self.p_markup(inner_html(element), self.style.paragraph)
            elif element.tag in 'ol':
                style = deepcopy(self.style.li)
                style.leftIndent += self.style.ol.leftIndent
                items = [
                    MarkupParagraph(inner_html(item), style)
                    for item in element
                ]
                self.story.append(
                    ListFlowable(
                        items,
                        bulletType=self.style.ol.bullet,
                        bulletFontName=self.style.li.fontName,
                        bulletFontSize=self.style.li.fontSize,
                        leftIndent=self.style.ol.liIndent,
                        bulletDedent=(
                            self.style.ol.liIndent - self.style.ol.leftIndent
                        )
                    )
                )
            elif element.tag == 'ul':
                style = deepcopy(self.style.li)
                style.leftIndent += self.style.ul.leftIndent
                items = [
                    MarkupParagraph(inner_html(item), style)
                    for item in element
                ]
                self.story.append(
                    ListFlowable(
                        items,
                        bulletType='bullet',
                        bulletFontName=self.style.li.fontName,
                        bulletFontSize=self.style.li.fontSize,
                        start=self.style.ul.bullet,
                        leftIndent=self.style.ul.liIndent,
                        bulletDedent=(
                            self.style.ul.liIndent - self.style.ul.leftIndent
                        )
                    )
                )
