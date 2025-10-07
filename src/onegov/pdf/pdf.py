from __future__ import annotations

from bleach.linkifier import LinkifyFilter
from bleach.sanitizer import Cleaner
from copy import deepcopy
from contextlib import contextmanager
from functools import partial
from html5lib.filters.whitespace import Filter as WhitespaceFilter
from io import StringIO
from lxml import etree
from onegov.core.utils import module_path
from onegov.pdf.flowables import InlinePDF
from onegov.pdf.page_functions import empty_page_fn
from onegov.pdf.templates import Template
from pdfdocument.document import Empty
from pdfdocument.document import MarkupParagraph
from pdfdocument.document import PDFDocument
from pdfdocument.document import register_fonts_from_paths
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.units import cm
from reportlab.platypus import Frame
from reportlab.platypus import Image
from reportlab.platypus import KeepTogether
from reportlab.platypus import ListFlowable
from reportlab.platypus import NextPageTemplate
from reportlab.platypus import PageTemplate
from reportlab.platypus import Paragraph
from reportlab.platypus import Table
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.tables import TableStyle
from uuid import uuid4


from typing import overload, Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath, SupportsRead
    from bleach.callbacks import _HTMLAttrs
    from bleach.sanitizer import _Filter
    from collections.abc import Iterable, Iterator, Sequence
    from reportlab.lib.styles import PropertySet
    from reportlab.platypus.doctemplate import _PageCallback
    from reportlab.platypus.tables import _TableCommand


TABLE_CELL_CHAR_LIMIT = 2000


class Pdf(PDFDocument):
    """ A PDF document. """

    default_link_color = '#00538c'
    toc: TableOfContents | None
    toc_numbering: dict[int, int]
    doc: Template

    def __init__(
        self,
        *args: Any,
        toc_levels: int = 3,
        created: str = '',
        logo: str | None = None,
        link_color: str | None = None,
        underline_links: bool = False,
        underline_width: float | str = 0.5,
        skip_numbering: bool = False,
        **kwargs: Any
    ):
        link_color = link_color or self.default_link_color
        underline_links = underline_links or False
        underline_width = str(underline_width)

        super().__init__(*args, **kwargs)

        self.doc = Template(*args, **kwargs)
        self.doc.PDFDocument = self
        self.doc.created = created  # type:ignore[attr-defined]
        self.doc.logo = logo  # type:ignore[attr-defined]

        self.toc = None
        self.toc_numbering = {}
        self.toc_levels = toc_levels
        self.link_color = link_color
        self.underline_links = underline_links
        self.underline_width = underline_width
        # hierarchical numbering for headings
        self.skip_numbering = skip_numbering

        # Use Source Sans 3 instead of Helvetica to support more special
        # characters; https://github.com/adobe-fonts/source-sans
        path = module_path('onegov.pdf', 'fonts')
        register_fonts_from_paths(
            font_name='Helvetica',
            regular=f'{path}/SourceSans3-Regular.ttf',
            italic=f'{path}/SourceSans3-It.ttf',
            bold=f'{path}/SourceSans3-Bold.ttf',
            bolditalic=f'{path}/SourceSans3-BoldIt.ttf',
        )

    def init_a4_portrait(
        self,
        page_fn: _PageCallback = empty_page_fn,
        page_fn_later: _PageCallback | None = None,
        *,
        font_size: int = 10,
        margin_left: float = 2.5 * cm,
        margin_right: float = 2.5 * cm,
        margin_top: float = 3 * cm,
        margin_bottom: float = 3 * cm,
    ) -> None:

        width = 21 * cm
        height = 29.7 * cm

        full_frame = Frame(
            margin_left,
            margin_top,
            width - margin_left - margin_right,
            height - margin_top - margin_bottom,
            showBoundary=self.show_boundaries,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
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

        self.adjust_style(font_size=font_size)

    def adjust_style(self, font_size: int = 10) -> None:
        """ Sets basic styling (borrowed from common browser defaults). """

        self.generate_style(
            font_name=self.font_name,
            font_size=font_size
        )

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

        # FIXME: Using a sequence of commands rather than an actual TableStyle
        #        seems bad, we can just use `getCommands` if we want to iterate
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

    @contextmanager
    def keep_together(self) -> Iterator[None]:
        """ Keeps anything added during the lifetime of this contextmanager
        together.

        Example::

            pdf = Pdf(file, author='OneGov')
            with pdf.keep_together():
                pdf.h1('Title')
                pdf.table([[...]])
            pdf.generate()

        """
        complete_story, self.story = self.story, []
        try:
            yield
        finally:
            complete_story.append(KeepTogether(self.story))
            self.story = complete_story

    def table_of_contents(self) -> None:
        """ Adds a table of contents.

        The entries are added automatically when adding headers. Example::

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

    def _add_toc_heading(
        self,
        text: str,
        style: PropertySet,
        level: int
    ) -> None:
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

            if not self.skip_numbering:
                # create and prepend the prefix
                prefix = '.'.join(
                    str(self.toc_numbering.get(idx)) or ''
                    for idx in range(level + 1)
                )
                text = f'{prefix} {text}'

            # create a link
            bookmark = uuid4().hex
            text = f'{text}<a name="{bookmark}"/>'

        self.story.append(Paragraph(text, style))

        # add the toc entry
        if self.toc is not None and level < self.toc_levels:
            self.story[-1].toc_level = level  # type:ignore[attr-defined]
            self.story[-1].bookmark = bookmark  # type:ignore[attr-defined]

    def h1(self, title: str, style: PropertySet | None = None) -> None:
        if title:
            style = style or self.style.heading1
            self._add_toc_heading(title, style, 0)

    def h2(self, title: str, style: PropertySet | None = None) -> None:
        if title:
            style = style or self.style.heading2
            self._add_toc_heading(title, style, 1)

    def h3(self, title: str, style: PropertySet | None = None) -> None:
        if title:
            style = style or self.style.heading3
            self._add_toc_heading(title, style, 2)

    def h4(self, title: str, style: PropertySet | None = None) -> None:
        if title:
            style = style or self.style.heading4
            self._add_toc_heading(title, style, 3)

    def h5(self, title: str, style: PropertySet | None = None) -> None:
        if title:
            style = style or self.style.heading5
            self._add_toc_heading(title, style, 4)

    def h6(self, title: str, style: PropertySet | None = None) -> None:
        if title:
            style = style or self.style.heading6
            self._add_toc_heading(title, style, 5)

    def h(self, title: str, level: int = 0) -> None:
        """ Adds a header according to the given level (h1-h6).

        Levels outside the supported range are added as paragraphs with h1/h6
        style (without appearing in the table of contents).

        """
        if title:
            if level < 1:
                self.p_markup(title, self.style.heading1)
            elif level < 7:
                getattr(self, f'h{level}')(title)
            else:
                self.p_markup(title, self.style.heading6)

    def fit_size(
        self,
        width: float,
        height: float,
        factor: float = 1.0
    ) -> tuple[float, float]:
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

    def image(
        self,
        # this may be too lax, but a short look at the source suggests
        # that read might be enough for this to work...
        filelike: StrOrBytesPath | SupportsRead[bytes],
        factor: float = 1.0
    ) -> None:
        """ Adds an image and fits it to the page. """
        image = Image(filelike, hAlign='LEFT')
        image._restrictSize(  # type:ignore[attr-defined]
            *self.fit_size(image.imageWidth, image.imageHeight, factor)
        )
        self.story.append(image)

    def pdf(
        self,
        filelike: StrOrBytesPath | SupportsRead[bytes],
        factor: float = 1.0
    ) -> None:
        """ Adds a PDF and fits it to the page. """

        pdf = InlinePDF(filelike, self.doc.width)
        if pdf.width and pdf.height:
            old = pdf.width
            pdf.width, pdf.height = self.fit_size(
                pdf.width, pdf.height, factor
            )
            pdf.scale = pdf.scale * pdf.width / old

            self.story.append(pdf)

    @overload  # type:ignore[override]
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | Sequence[float | None] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        ratios: Literal[False] = False
    ) -> None: ...

    @overload
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | list[float] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        *,
        ratios: Literal[True]
    ) -> None: ...

    @overload
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | list[float] | None,
        style: TableStyle | Iterable[_TableCommand] | None,
        ratios: Literal[True]
    ) -> None: ...

    @overload
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | Sequence[float | None] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        ratios: bool = False
    ) -> None: ...

    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | Sequence[float | None] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        ratios: bool = False
    ) -> None:
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
            total = sum(columns)  # type:ignore[arg-type]
            columns = [
                self.doc.width * p / total  # type:ignore
                for p in columns
            ]

        tdata = [
            [
                cell if isinstance(cell, Paragraph) else
                MarkupParagraph(cell, deepcopy(self.style.normal))
                for cell in row
            ]
            for row in data
        ]

        # Copy the alignments from the table to the paragraphs
        def adjust(value: int) -> int | None:
            if value == -1:
                return None
            if value < 0:
                return value + 1
            return value

        alignments: dict[str, Literal[0, 1, 2]] = {
            'CENTER': TA_CENTER,
            'LEFT': TA_LEFT,
            'RIGHT': TA_RIGHT,
        }

        style = style or self.style.table
        if isinstance(style, TableStyle):
            style = style.getCommands()

        # FIXME: We need a tagged union in types-reportlab for fewer issues
        st: Any
        for st in style:
            if st[0] in ('ALIGN', 'ALIGNMENT'):
                for row in tdata[adjust(st[1][1]):adjust(st[2][1])]:
                    for cell in row[adjust(st[1][0]):adjust(st[2][0])]:
                        cell.style.alignment = alignments.get(st[3], TA_CENTER)

        self.story.append(Table(tdata, columns, style=style))

    def figcaption(
        self,
        text: str,
        style: PropertySet | None = None
    ) -> None:
        """ Adds a figure caption. """

        self.p_markup(text, style=style or self.style.figcaption)

    @staticmethod
    # Walk the tree and convert the elements
    def strip(text: str) -> str:
        text = text.strip('\r\n')
        prefix = ' ' if text.startswith(' ') else ''
        postfix = ' ' if text.endswith(' ') else ''

        # some characters cause issues in the Reportlab and pdfdocument
        # library, so we need to escape them
        text = text.replace(';', '&#59;')

        return prefix + text.strip() + postfix

    @staticmethod
    def inner_html(element: etree._Element) -> str:
        return '{}{}{}'.format(
            Pdf.strip(element.text or ''),
            ''.join(
                Pdf.strip(etree.tostring(child, encoding='unicode'))
                for child in element
            ),
            Pdf.strip(element.tail or '')
        )

    def mini_html(self, html: str | None, linkify: bool = False) -> None:
        """ Convert a small subset of HTML into ReportLab paragraphs.

        This is very limited and currently supports only links, paragraphs and
        non-nested ordered/unordered lists.

        If linkifing is enabled, a-tags are cleaned and kept and the html is
        linkified automatically.

        """

        if not html or html == '<p></p>':
            return

        # Remove unwanted markup
        tags = ['p', 'br', 'strong', 'b', 'em', 'li', 'ol', 'ul', 'li']
        attributes = {}
        filters: list[_Filter] = [WhitespaceFilter]

        if linkify:
            link_color = self.link_color
            underline_links = self.underline_links
            underline_width = self.underline_width

            def colorize(
                attrs: _HTMLAttrs,
                new: bool = False
            ) -> _HTMLAttrs:
                # phone numbers appear here but are escaped, skip...
                if not attrs.get((None, 'href')):
                    # FIXME: bleach stubs seem to be incorrect here
                    #        but we may be able to just return attrs
                    return None  # type:ignore[return-value]
                attrs[(None, 'color')] = link_color
                if underline_links:
                    attrs[(None, 'underline')] = '1'
                    attrs[('a', 'underlineColor')] = link_color
                    attrs[('a', 'underlineWidth')] = underline_width
                return attrs

            tags.append('a')
            attributes['a'] = ['href']
            filters.append(
                partial(
                    LinkifyFilter, parse_email=True, callbacks=[colorize])
            )

        cleaner = Cleaner(
            tags=tags,
            attributes=attributes,
            strip=True,
            filters=filters
        )
        html = cleaner.clean(html)
        # Todo: phone numbers with href="tel:.." are cleaned out

        tree = etree.parse(StringIO(html), etree.HTMLParser())
        body = tree.find('body')
        if body is None:
            return

        if body.text and body.text.strip():
            self.p(body.text, self.style.paragraph)

        for element in body:
            if element.tag == 'p':
                self.p_markup(self.inner_html(element), self.style.paragraph)
            elif element.tag == 'ol':
                style = deepcopy(self.style.li)
                style.leftIndent += self.style.ol.leftIndent
                items = [
                    MarkupParagraph(self.inner_html(item), style)
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
                    MarkupParagraph(self.inner_html(item), style)
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

            if element.tail and element.tail.strip():
                self.p(element.tail, self.style.paragraph)
