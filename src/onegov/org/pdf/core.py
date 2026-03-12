from __future__ import annotations

from copy import deepcopy

from onegov.org import _
from onegov.pdf import Pdf, page_fn_header
from pdfdocument.document import MarkupParagraph
from reportlab.lib import colors
from reportlab.platypus import Paragraph


from typing import overload, Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from gettext import GNUTranslations
    from onegov.pdf.templates import Template
    from reportlab.lib.styles import PropertySet
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus.tables import _TableCommand, TableStyle


class OrgPdf(Pdf):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        locale = kwargs.pop('locale', None)
        self.locale: str = locale or 'en'
        translations = kwargs.pop('translations', None)
        super().__init__(*args, **kwargs)
        self.translations: dict[str, GNUTranslations] = translations

        # Modification for the footer left on all pages
        self.doc.author = self.translate(_('Source')) + f': {self.doc.author}'

    def translate(self, text: str) -> str:
        """ Translates the given string. """

        if not hasattr(text, 'interpolate'):
            return text

        translator = (
            self.translations.get(self.locale)
            if self.locale else None
        )
        translated = translator.gettext(text) if translator else text
        return text.interpolate(translated)

    def h1(self, title: str) -> None:  # type:ignore[override]
        """ Translated H1. """

        super().h1(self.translate(title))

    def h2(self, title: str) -> None:  # type:ignore[override]
        """ Translated H2. """

        super().h2(self.translate(title))

    def h3(self, title: str) -> None:  # type:ignore[override]
        """ Translated H3. """

        super().h3(self.translate(title))

    @staticmethod
    def page_fn_header_and_footer(
        canvas: Canvas,
        doc: Template
    ) -> None:

        page_fn_header(canvas, doc)

        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        if doc.author:
            canvas.drawString(
                doc.leftMargin,
                doc.bottomMargin / 2,
                f'{doc.author}'
            )
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin / 2,
            f'{canvas.getPageNumber()}'
        )
        canvas.restoreState()

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        return self.page_fn_header_and_footer

    @property
    def page_fn_later(self) -> Callable[[Canvas, Template], None]:
        return self.page_fn_header_and_footer

    @overload  # type:ignore[override]
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | Sequence[float | None] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        ratios: Literal[False] = False,
        border: bool = True,
        first_bold: bool = True
    ) -> None: ...

    @overload
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | list[float] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        *,
        ratios: Literal[True],
        border: bool = True,
        first_bold: bool = True
    ) -> None: ...

    @overload
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | list[float] | None,
        style: TableStyle | Iterable[_TableCommand] | None,
        ratios: Literal[True],
        border: bool = True,
        first_bold: bool = True
    ) -> None: ...

    @overload
    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | Sequence[float | None] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        ratios: bool = False,
        border: bool = True,
        first_bold: bool = True
    ) -> None: ...

    def table(
        self,
        data: Sequence[Sequence[str | Paragraph]],
        columns: Literal['even'] | Sequence[float | None] | None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        ratios: bool = False,
        border: bool = True,
        first_bold: bool = True
    ) -> None:

        if border:
            # FIXME: What if we want to pass a style in?
            style = list(self.style.table)
            style.append(('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.black))
        if not first_bold:
            return super().table(data, columns, style, ratios)
        for row in data:
            if isinstance(row[0], Paragraph):
                continue
            row[0] = MarkupParagraph(  # type:ignore[index]
                self.translate(row[0]), style=deepcopy(self.style.bold))
        return super().table(data, columns, style, ratios)

    def p_markup(
        self,
        text: str,
        style: PropertySet | None = None
    ) -> None:

        super().p_markup(self.translate(text), style)
