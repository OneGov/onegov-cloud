from bleach.sanitizer import Cleaner
from copy import deepcopy
from html5lib.filters.whitespace import Filter as whitespace_filter
from io import StringIO
from lxml import etree
from onegov.pdf.flowables import InlinePDF
from onegov.pdf.page_functions import empty_page_fn
from onegov.pdf.templates import Template
from pdfdocument.document import Empty
from pdfdocument.document import MarkupParagraph
from pdfdocument.document import PDFDocument
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.units import cm
from reportlab.platypus import Frame
from reportlab.platypus import Image
from reportlab.platypus import ListFlowable
from reportlab.platypus import NextPageTemplate
from reportlab.platypus import PageTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Table
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.tables import TableStyle
from uuid import uuid4


class Pdf(PDFDocument):
    """ A PDF document. """

    def __init__(self, *args, **kwargs):
        toc_levels = kwargs.pop('toc_levels', 3)
        created = kwargs.pop('created', '')

        super(Pdf, self).__init__(*args, **kwargs)

        self.doc = Template(*args, **kwargs)
        self.doc.PDFDocument = self
        self.doc.created = created

        self.toc = None
        self.toc_numbering = {}
        self.toc_levels = toc_levels

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

        self.style.heading5 = deepcopy(self.style.normal)
        self.style.heading5.fontSize = 1 * self.style.fontSize
        self.style.heading5.spaceBefore = 1 * self.style.heading5.fontSize
        self.style.heading5.spaceAfter = 1 * self.style.heading5.fontSize
        self.style.heading5.fontName = self.style.fontName
        self.style.heading5.textColor = self.style.normal.textColor
        self.style.heading5.leading = 1.2 * self.style.heading5.fontSize

        self.style.heading6 = deepcopy(self.style.normal)
        self.style.heading6.fontSize = 1 * self.style.fontSize
        self.style.heading6.spaceBefore = 0.67 * self.style.heading6.fontSize
        self.style.heading6.spaceAfter = 0.67 * self.style.heading6.fontSize
        self.style.heading6.fontName = self.style.fontName
        self.style.heading6.textColor = self.style.normal.textColor
        self.style.heading6.leading = 1.2 * self.style.heading6.fontSize

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

    def table_of_contents(self):
        """ Adds a table of contents.

        The entries are added automatically when adding headers. Example:

            pdf = Pdf(file, author='OneGov', toc_levels=2)
            pdf.init_a4_portrait(page_fn=draw_header)
            pdf.table_of_contents()
            pdf.h1('Title')
            pdf.generate()

        """

        self.toc = TableOfContents()
        self.toc.levelStyles[0].leftIndent = 0
        self.toc.levelStyles[0].rightIndent = 0.25 * cm
        self.toc.levelStyles[0].fontName = self.font_name
        self.toc.levelStyles[0].fontName = f'{self.font_name}-Bold'
        self.toc.levelStyles[0].spaceBefore = 0.2 * cm
        for idx in range(1, 7):
            toc_style = deepcopy(self.toc.levelStyles[0])
            toc_style.name = f'Level {idx}'
            toc_style.fontName = self.font_name
            toc_style.spaceBefore = 0
            self.toc.levelStyles.append(toc_style)

        self.toc.dotsMinLevel = 7
        self.toc.tableStyle = TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0.2 * cm)
        ])
        self.story.append(self.toc)

    def _add_toc_heading(self, text, style, level):
        """ Adds a heading with automatically adding an entry to the table of
        contents.

        """
        if self.toc is not None:
            # increment current level
            self.toc_numbering.setdefault(level, 0)
            self.toc_numbering[level] += 1

            # reset higher levels
            for idx in range(level + 1, max(self.toc_numbering.keys()) + 1):
                self.toc_numbering[idx] = 0

            # create and prepend the prefix
            prefix = '.'.join([
                str(self.toc_numbering.get(idx)) or ''
                for idx in range(level + 1)
            ])
            text = f'{prefix} {text}'

            # create a link
            bookmark = uuid4().hex
            text = f'{text}<a name="{bookmark}"/>'

        self.story.append(Paragraph(text, style))

        # add the toc entry
        if self.toc is not None and level < self.toc_levels:
            self.story[-1].toc_level = level
            self.story[-1].bookmark = bookmark

    def h1(self, text, style=None):
        style = style or self.style.heading1
        self._add_toc_heading(text, style, 0)

    def h2(self, text, style=None):
        style = style or self.style.heading2
        self._add_toc_heading(text, style, 1)

    def h3(self, text, style=None):
        style = style or self.style.heading3
        self._add_toc_heading(text, style, 2)

    def h4(self, text, style=None):
        style = style or self.style.heading4
        self._add_toc_heading(text, style, 3)

    def h5(self, text, style=None):
        style = style or self.style.heading5
        self._add_toc_heading(text, style, 4)

    def h6(self, text, style=None):
        style = style or self.style.heading6
        self._add_toc_heading(text, style, 5)

    def h(self, title, level=0):
        """ Adds a header according to the given level (h1-h6).

        Levels outside the supported range are added as paragraphs with h1/h6
        style (without appearing in the table of contents).

        """

        if level < 1:
            self.p_markup(title, self.style.heading1)
        elif level < 7:
            getattr(self, f'h{level}')(title)
        else:
            self.p_markup(title, self.style.heading6)

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

    def image(self, filelike, factor=1.0):
        """ Adds an image and fits it to the page. """

        image = Image(filelike, hAlign='LEFT')
        image._restrictSize(
            *self.fit_size(image.imageWidth, image.imageHeight, factor)
        )
        self.story.append(image)

    def pdf(self, filelike, factor=1.0):
        """ Adds a PDF and fits it to the page. """

        pdf = InlinePDF(filelike, self.doc.width)
        if pdf.width and pdf.height:
            old = pdf.width
            pdf.width, pdf.height = self.fit_size(
                pdf.width, pdf.height, factor
            )
            pdf.scale = pdf.scale * pdf.width / old

            self.story.append(pdf)

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
