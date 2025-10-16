from __future__ import annotations

from copy import deepcopy
from datetime import date
from functools import partial
from io import BytesIO, StringIO

from bleach import Cleaner
from bleach.linkifier import LinkifyFilter
from lxml import etree
from markupsafe import Markup
from onegov.chat import MessageCollection
from onegov.org import _
from onegov.org.constants import (
    INVOICE_GROUPS, PAYMENT_STATES, PAYMENT_SOURCES, TICKET_STATES)
from onegov.org.layout import DefaultLayout, TicketLayout
from onegov.org.models.ticket import ticket_submitter
from onegov.org.utils import group_invoice_items
from onegov.org.views.message import view_messages_feed
from onegov.pdf import Pdf, page_fn_header
from onegov.qrcode import QrCode
from html5lib.filters.whitespace import Filter as WhitespaceFilter
from pdfdocument.document import MarkupParagraph
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import PageBreak, Paragraph


from typing import overload, Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from collections.abc import Collection
    from bleach.callbacks import _HTMLAttrs
    from bleach.sanitizer import _Filter
    from gettext import GNUTranslations
    from onegov.org.forms import TicketInvoiceSearchForm
    from onegov.org.request import OrgRequest
    from onegov.pdf.templates import Template
    from onegov.ticket import Ticket
    from reportlab.lib.styles import PropertySet
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus.tables import _TableCommand, TableStyle


class TicketQrCode(QrCode):
    _border = 0


class TicketPdf(Pdf):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        locale = kwargs.pop('locale', None)
        self.locale: str = locale or 'en'
        translations = kwargs.pop('translations', None)
        qr_payload = kwargs.pop('qr_payload', None)
        super().__init__(*args, **kwargs)
        self.translations: dict[str, GNUTranslations] = translations

        # Modification for the footer left on all pages
        self.doc.author = self.translate(_('Source')) + f': {self.doc.author}'
        self.doc.qr_payload = qr_payload  # type:ignore[attr-defined]

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

    @staticmethod
    def page_fn_header_and_footer_qr(
        canvas: Canvas,
        doc: Template
    ) -> None:

        assert hasattr(doc, 'qr_payload')
        TicketPdf.page_fn_header_and_footer(canvas, doc)
        height = 2 * cm
        width = height
        canvas.saveState()
        # 0/0 is bottom left
        image = ImageReader(TicketQrCode.from_payload(doc.qr_payload))
        canvas.drawImage(
            image,
            x=doc.pagesize[0] - doc.rightMargin - width,
            y=doc.pagesize[1] - doc.topMargin - height,
            width=width,
            height=height,
            mask='auto')
        canvas.restoreState()

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        """ First page the same as later except Qr-Code. """
        return self.page_fn_header_and_footer_qr

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

    def ticket_summary(self, html: str | None, linkify: bool = True) -> None:
        """A copy of the mini_html adapted for ticket summary.
        We have to guarantee some backwards compatibility here whenever
        we change the templates and thereby the snapshot of tickets.

        Must work for templates:
        - directory_entry_submission
        - display_event
        - display_form
        - reservations

        """
        if not html or html == '<p></p>':
            return

        # Remove unwanted markup
        tags = ['p', 'br', 'strong', 'b', 'em', 'li', 'ol', 'ul', 'li']
        ticket_summary_tags = ['dl', 'dt', 'dd', 'h2']
        tags += ticket_summary_tags

        attributes: dict[str, list[str]] = {}
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
                    # FIXME: The bleach stubs appear to be incorrect
                    #        since this definitely works at runtime
                    #        but we may be able to return an empty
                    #        dictionary or attrs instead of None
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

        body_element = tree.find('body')
        assert body_element is not None
        for element in body_element:
            if element.tag == 'dl':
                data: list[list[Paragraph | str]] = []
                for item in element:
                    if item.tag == 'dt':
                        p = MarkupParagraph(
                            self.inner_html(item), self.style.bold)
                        data.append([p, ''])
                    if item.tag == 'dd':
                        data[-1][1] = MarkupParagraph(self.inner_html(item))
                if data:
                    self.table(data, 'even')
            elif element.tag == 'h2':
                # Fieldset titles
                self.h2(self.inner_html(element))

            elif element.tag == 'ul':
                items = [
                    [MarkupParagraph(self.inner_html(item))]
                    for item in element
                ]
                self.table(items, 'even')

    def ticket_metadata(self, ticket: Ticket, layout: TicketLayout) -> None:
        handler = ticket.handler
        group = handler.group or ticket.group
        created_dt = layout.to_timezone(ticket.created, layout.timezone)
        created = layout.format_date(created_dt, 'datetime')

        if hasattr(ticket, 'reference_group'):
            subject = ticket.reference_group(layout.request)
        else:
            subject = ticket.title

        submitter = ticket_submitter(ticket)
        ticket_state = self.translate(TICKET_STATES[ticket.state])
        owner = ticket.user.username if ticket.user else ''

        def seconds(time: float | None) -> str:
            return layout.format_seconds(time) if time else ''

        meta_fields = {
            'submitter_name': _('Name'),
            'submitter_address': _('Address'),
            'submitter_phone': _('Phone')
        }

        # pep572 still a cool thing
        submitter_meta = [
            [text, layout.linkify(value)]
            for field, text in meta_fields.items()
            if (value := getattr(handler, field))
        ]

        data = [
            [_('Subject'), subject],
            [_('Submitter'), submitter],
            *submitter_meta,
            [_('State'), ticket_state],
            [_('Group'), group],
            [_('Owner'), owner],
            [_('Created'), created],
            [_('Reaction Time'), seconds(ticket.reaction_time)],
            [_('Process Time'), seconds(ticket.process_time)],
        ]

        # In case of imported events..
        event_source = handler.data.get('source')
        if event_source and layout.request.is_manager:
            data.append([self.translate(_('Event Source')), event_source])

        self.table(data, 'even')

    def ticket_invoice(self, ticket: Ticket, layout: TicketLayout) -> None:
        invoice = ticket.invoice
        if not invoice:
            return

        show_cost_object = any(item.cost_object for item in invoice.items)
        show_quantity = any(item.quantity != 1.0 for item in invoice.items)
        show_vat = any(item.vat for item in invoice.items)
        item_groups = group_invoice_items(invoice.items)
        headers = [_('Booking Text')]
        totals: list[Paragraph | str] = [
            MarkupParagraph(
                self.translate(_('Total')),
                style=deepcopy(self.style.bold)
            )
        ]
        ratios: list[float] = []
        if show_cost_object:
            headers.append(_('Cost center / cost unit'))
            totals.append('')
            ratios.append(20.0)
        if show_quantity:
            headers.extend((
                _('Unit'),
                _('Quantity'),
            ))
            totals.extend(('', ''))
            ratios.extend((12.0, 12.0))
        if show_vat:
            headers.extend((
                _('VAT Rate'),
                _('VAT'),
            ))
            totals.extend(('', layout.format_number(invoice.total_vat, 2)))
            ratios.extend((12.0, 12.0))
        headers.append(_('Amount'))
        totals.append(layout.format_number(invoice.total_amount, 2))
        ratios.append(12.0)
        ratios.insert(0, 100.0 - sum(ratios))
        num_cols = len(headers)
        base_style: list[_TableCommand] = [
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (1, -1), 2),
            ('LEFTPADDING', (1, 0), (-1, -1), 0),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 2),
            ('RIGHTPADDING', (-2, 0), (-2, -1), 0),
            ('FIRSTLINEINDENT', (0, 0), (-1, -1), 0),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (1 + show_cost_object, -1), 'LEFT'),
            ('ALIGN', (1 + show_cost_object, 0), (-1, -1), 'RIGHT'),
        ]
        head_style = base_style[:]
        head_style.extend((
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('LINEBELOW', (0, 0), (-1, 0), 0.2, colors.black),
        ))
        group_style = base_style[:]
        group_style.extend((
            ('SPAN', (0, 0), (-1, 0)),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [
                colors.whitesmoke,
                colors.white
            ]),
            ('LINEABOVE', (0, 0), (-1, 0), 0.2, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 0.2, colors.black),
        ))
        footer_style = base_style[:]
        footer_style.extend((
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('LINEABOVE', (0, 0), (-1, 0), 0.2, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 0.2, colors.black),
        ))

        with self.keep_together():
            self.h2(_('Invoice'))
            if invoice.invoicing_party:
                self.table([[
                    self.translate(_('Invoicing party')),
                    MarkupParagraph(Markup('<br/>').join(
                        invoice.invoicing_party.splitlines()
                    ))
                ]], [ratios[0], 100 - ratios[0]], ratios=True, border=False)
                self.spacer()
            self.table(
                [[
                    MarkupParagraph(
                        self.translate(h),
                        style=deepcopy(self.style.bold)
                    )
                    for h in headers
                ]],
                ratios,
                ratios=True,
                border=False,
                style=head_style,
                first_bold=False
            )
            for group, items in item_groups.items():
                data = [[
                    MarkupParagraph(
                        self.translate(INVOICE_GROUPS[group]),
                        style=deepcopy(self.style.bold)
                    ),
                    *(('') * (num_cols - 1))
                ]]
                for item in items:
                    column = [item.text]
                    if show_cost_object:
                        column.append(item.cost_object or '')
                    if show_quantity:
                        column.extend((
                            layout.format_number(item.unit, 2),
                            layout.format_number(item.quantity, 2),
                        ))
                    if show_vat:
                        column.extend((
                            f'{layout.format_number(item.vat_rate or 0, 1)}%',
                            layout.format_number(item.vat, 2),
                        ))
                    column.append(layout.format_number(item.amount, 2))
                    data.append(column)
                self.table(
                    data,
                    ratios,
                    ratios=True,
                    border=False,
                    style=group_style,
                    first_bold=False
                )
            self.table(
                [totals],
                ratios,
                ratios=True,
                border=False,
                style=footer_style,
                first_bold=False
            )

    def ticket_payment(self, ticket: Ticket, layout: TicketLayout) -> None:
        price = ticket.handler.payment
        if not price:
            return
        state = self.translate(PAYMENT_STATES[price.state])
        # credit card
        self.h2(_('Payment'))
        amount = f'{layout.format_number(price.net_amount)}'
        self.table([
            [_('Total Amount'), f'{amount} {price.currency}'],
            [_('State'), state],
            [_('Source'), self.translate(PAYMENT_SOURCES[price.source])],
            [_('Fee'), f'{layout.format_number(price.fee)}'],
        ], 'even')

    def p_markup(
        self,
        text: str,
        style: PropertySet | None = None
    ) -> None:

        super().p_markup(self.translate(text), style)

    def ticket_timeline(self, msg_feed: Mapping[str, Any] | None) -> None:
        """Will parse the timeline from view_messages_feed """
        if not msg_feed or not msg_feed['messages']:
            return

        tables: dict[str, list[list[str | None]]] = {}
        for msg in reversed(msg_feed['messages']):
            table = tables.setdefault(msg['date'], [])

            row = self.extract_feed_info(msg['html'])
            if row is None:
                continue

            table.append(row)

        for date_, data in tables.items():
            self.h4(date_)
            # FIXME: Why does `None` work? is it because of `MarkupParagraph`
            #        internals? Why not use an empty string? Does that do
            #        something different?
            self.table(data, 'even', first_bold=False)  # type:ignore

    @staticmethod
    def extract_feed_info(html: str) -> list[str | None] | None:
        """ Must be able to parse templates message_{message.type}.pt and
        return the useful data in cleaned form.
        """
        if not html or html == '<p></p>':
            return None

        # Remove unwanted markup
        tags = ['p', 'br', 'strong', 'b', 'em', 'li', 'ol', 'ul', 'li']
        ticket_summary_tags = ['dl', 'dt', 'dd', 'h2', 'div']
        tags += ticket_summary_tags

        attributes = {}
        filters = [WhitespaceFilter]
        attributes['div'] = ['class']

        cleaner = Cleaner(
            tags=tags,
            attributes=attributes,
            strip=True,
            filters=filters
        )
        html = cleaner.clean(html)
        tree = etree.parse(StringIO(html), etree.HTMLParser())
        data = []

        body_element = tree.find('body')
        assert body_element is not None
        for el in body_element:
            if el.tag == 'div':
                class_ = el.attrib['class']
                if class_ == 'timestamp':
                    data = [TicketPdf.inner_html(el), None]
                if class_ == 'text':
                    data[1] = TicketPdf.inner_html(el)
        return data

    def add_ticket(self, ticket: Ticket, request: OrgRequest) -> None:
        """ Adds a ticket to the story. """

        layout = TicketLayout(ticket, request)
        handler = ticket.handler

        self.h(f'{request.translate(_("Ticket"))} {ticket.number}')
        self.spacer()

        deleted_message = None
        if handler.deleted:
            summary = ticket.snapshot.get('summary')
            deleted_message = _('The record behind this ticket was removed. '
                                'The following information is a snapshot '
                                'kept for future reference.')
        else:
            summary = handler.get_summary(request)

        self.ticket_metadata(ticket, layout)

        self.h1(_('Summary'))
        if deleted_message:
            self.p(self.translate(deleted_message))
            self.spacer()
        self.ticket_summary(summary)
        self.ticket_invoice(ticket, layout)
        self.ticket_payment(ticket, layout)

        # If used for the user instead of the manager...
        messages = MessageCollection(
            request.session,
            channel_id=ticket.number
        )
        if not request.is_manager:
            messages.type = request.app.settings.org.public_ticket_messages

        self.h1(request.translate(_('Timeline')))
        self.ticket_timeline(view_messages_feed(messages, request))

    @classmethod
    def from_ticket(
        cls,
        request: OrgRequest,
        ticket: Ticket
    ) -> BytesIO:
        """
        Creates a PDF representation of the ticket. It is sensible to the
        templates used to render the message feed and the summary of the ticket
        coming from ticket handler. With this approach, snapshotted
        summaries are supported.
        """
        result = BytesIO()
        pdf = cls(
            result,
            title=ticket.number,
            created=f'{date.today():%d.%m.%Y}',
            link_color='#00538c',
            underline_links=True,
            author=request.host_url,
            translations=request.app.translations,
            locale=request.locale,
            qr_payload=request.link(
                ticket,
                name='' if request.is_manager_for_model(ticket) else 'status'
            )
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )
        pdf.add_ticket(ticket, request)

        pdf.generate()
        result.seek(0)
        return result


class TicketsPdf(TicketPdf):

    def filter_info(
        self,
        form: TicketInvoiceSearchForm,
        request: OrgRequest
    ) -> None:
        if not any((
            form.ticket_group.data,
            form.ticket_start_date.data,
            form.ticket_end_date.data,
            form.reservation_start_date.data,
            form.reservation_end_date.data,
        )):
            return

        layout = DefaultLayout(None, request)
        self.h1(_('Filters'))

        data: list[list[str | Paragraph]] = []
        if form.ticket_group.data:
            label_dict = {
                value: label
                for value, label, *__ in form.ticket_group.iter_choices()
            }
            data.append([
                self.translate(form.ticket_group.label.text),
                MarkupParagraph(Markup('<br/>').join(
                    label_dict.get(choice, choice)
                    for choice in form.ticket_group.data
                ))
            ])

        if form.ticket_start_date.data or form.ticket_end_date.data:
            data.extend([
                [
                    self.translate(form.ticket_start_date.label.text),
                    layout.format_date(form.ticket_start_date.data, 'date')
                ],
                [
                    self.translate(form.ticket_end_date.label.text),
                    layout.format_date(form.ticket_end_date.data, 'date')
                ],
            ])

        if form.reservation_start_date.data or form.reservation_end_date.data:
            data.extend([
                [
                    self.translate(form.reservation_start_date.label.text),
                    layout.format_date(
                        form.reservation_start_date.data, 'date')
                ],
                [
                    self.translate(form.reservation_end_date.label.text),
                    layout.format_date(form.reservation_end_date.data, 'date')
                ],
            ])
        self.table(data, 'even')
        self.story.append(PageBreak())

    @classmethod
    def from_tickets(
        cls,
        request: OrgRequest,
        tickets: Collection[Ticket],
        form: TicketInvoiceSearchForm | None = None
    ) -> BytesIO:
        """
        Creates a PDF representation of the tickets. It is sensible to the
        templates used to render the message feed and the summary of the ticket
        coming from ticket handler. With this approach, snapshotted
        summaries are supported.
        """

        result = BytesIO()
        title = request.translate(_('Tickets'))
        pdf = cls(
            result,
            title=title,
            created=f'{date.today():%d.%m.%Y}',
            link_color='#00538c',
            underline_links=True,
            author=request.host_url,
            translations=request.app.translations,
            locale=request.locale
        )

        pdf.init_a4_portrait(
            page_fn=pdf.page_fn_later, page_fn_later=pdf.page_fn_later
        )

        if form is not None:
            pdf.filter_info(form, request)

        for i, ticket in enumerate(tickets):
            # Only add page break after the first ticket
            if i > 0:
                pdf.story.append(PageBreak())

            pdf.add_ticket(ticket, request)

        pdf.generate()
        result.seek(0)
        return result
