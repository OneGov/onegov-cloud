from copy import deepcopy
from pdfdocument.document import MarkupParagraph, PDFDocument
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Flowable
from reportlab.platypus import Paragraph
from reportlab.platypus import Table
from reportlab.platypus import PageTemplate
from reportlab.platypus import Frame
from reportlab.platypus import NextPageTemplate
from reportlab.lib.units import cm


class InlinePDF(Flowable):
    """ A flowable containing a PDF. """

    def __init__(self, pdf_file, width):
        Flowable.__init__(self)
        pdf_file.seek(0)
        page = PdfReader(pdf_file, decompress=False).pages[0]
        self.page = pagexobj(page)
        self.scale = width / self.page.BBox[2]
        self.width = width
        self.height = self.page.BBox[3] * self.scale
        self.hAlign = 'CENTER'

    def wrap(self, *args):
        return (self.width, self.height)

    def draw(self):
        rl_obj = makerl(self.canv, self.page)
        self.canv.scale(self.scale, self.scale)
        self.canv.doForm(rl_obj)


def empty_page_fn(cavnas, doc):
    pass


class Pdf(PDFDocument):
    """ A PDF document. """

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

        self.style.heading2.fontSize = 1.5 * self.style.fontSize
        self.style.heading2.spaceBefore = 0.83 * self.style.heading2.fontSize
        self.style.heading2.spaceAfter = 0.83 * self.style.heading2.fontSize
        self.style.heading2.fontName = self.style.fontName
        self.style.heading2.textColor = self.style.normal.textColor

        self.style.heading3.fontSize = 1.17 * self.style.fontSize
        self.style.heading3.spaceBefore = 1 * self.style.heading3.fontSize
        self.style.heading3.spaceAfter = 1 * self.style.heading3.fontSize
        self.style.heading3.fontName = self.style.fontName
        self.style.heading3.textColor = self.style.normal.textColor

        self.style.paragraph.spaceAfter = 2 * self.style.paragraph.fontSize

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
