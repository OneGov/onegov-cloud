from onegov.org import _
from datetime import date
from functools import partial
from io import BytesIO, StringIO

from bleach import Cleaner
from bleach.linkifier import LinkifyFilter
from lxml import etree
from pdfdocument.document import MarkupParagraph
from reportlab.platypus import Paragraph

from onegov.chat import MessageCollection
from onegov.org.constants import TICKET_STATES, PAYMENT_STATES, PAYMENT_SOURCES
from onegov.org.layout import TicketLayout
from onegov.org.models.ticket import ticket_submitter
from onegov.org.views.message import view_messages_feed
from onegov.pdf import Pdf, page_fn_header
from html5lib.filters.whitespace import Filter as whitespace_filter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader


from onegov.qrcode import QrCode


class TicketQrCode(QrCode):
    _border = 0


class TicketPdf(Pdf):

    def __init__(self, *args, **kwargs):
        locale = kwargs.pop('locale', None)
        translations = kwargs.pop('translations', None)
        ticket = kwargs.pop('ticket')
        layout = kwargs.pop('layout')
        qr_payload = kwargs.pop('qr_payload')
        super(TicketPdf, self).__init__(*args, **kwargs)
        self.ticket = ticket
        self.locale = locale
        self.translations = translations
        self.layout = layout

        # Modification for the footer left on all pages
        self.doc.author = self.translate(_("Source")) + f': {self.doc.author}'
        self.doc.qr_payload = qr_payload

    def translate(self, text):
        """ Translates the given string. """

        if not hasattr(text, 'interpolate'):
            return text
        translator = self.translations.get(self.locale)
        return text.interpolate(translator.gettext(text))

    def h1(self, title):
        """ Translated H1. """

        super(TicketPdf, self).h1(self.translate(title))

    def h2(self, title):
        """ Translated H2. """

        super(TicketPdf, self).h2(self.translate(title))

    def h3(self, title):
        """ Translated H3. """

        super(TicketPdf, self).h3(self.translate(title))

    @staticmethod
    def page_fn_header_and_footer(canvas, doc):

        page_fn_header(canvas, doc)

        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        if doc.author:
            canvas.drawString(
                doc.leftMargin,
                doc.bottomMargin / 2,
                '{}'.format(doc.author)
            )
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin / 2,
            f'{canvas._pageNumber}'
        )
        canvas.restoreState()

    @staticmethod
    def page_fn_header_and_footer_qr(canvas, doc):
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
    def page_fn(self):
        """ First page the same as later except Qr-Code ..."""
        return self.page_fn_header_and_footer_qr

    @property
    def page_fn_later(self):
        return self.page_fn_header_and_footer

    def table(self, data, columns, style=None, ratios=False, border=True,
              first_bold=True):
        if border:
            style = list(self.style.table)
            style.append(('LINEBELOW', (0, 0), (-1, -1), 0.25, colors.black))
        if not first_bold:
            return super().table(data, columns, style, ratios)
        for row in data:
            if isinstance(row[0], Paragraph):
                continue
            row[0] = MarkupParagraph(
                self.translate(row[0]), style=self.style.bold)
        return super().table(data, columns, style, ratios)

    def ticket_summary(self, html, linkify=True):
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

        attributes = {}
        filters = [whitespace_filter]

        if linkify:
            link_color = self.link_color
            underline_links = self.underline_links
            underline_width = self.underline_width

            def colorize(attrs, new=False):
                # phone numbers appear here but are escaped, skip...
                if not attrs.get((None, 'href')):
                    return
                attrs[(None, u'color')] = link_color
                if underline_links:
                    attrs[(None, u'underline')] = '1'
                    attrs[('a', u'underlineColor')] = link_color
                    attrs[('a', u'underlineWidth')] = underline_width
                return attrs

            tags.append('a')
            attributes['a'] = ('href',)
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

        for element in tree.find('body'):
            if element.tag == 'dl':
                columns = 'even'
                data = []
                for item in element:
                    if item.tag == 'dt':
                        p = MarkupParagraph(
                            self.inner_html(item), self.style.bold)
                        data.append([p, None])
                    if item.tag == 'dd':
                        data[-1][1] = MarkupParagraph(self.inner_html(item))
                if data:
                    self.table(data, columns)
            elif element.tag == 'h2':
                # Fieldset titles
                self.h2(self.inner_html(element))

            elif element.tag == 'ul':
                items = [
                    [MarkupParagraph(self.inner_html(item))]
                    for item in element
                ]
                self.table(items, 'even')

    def ticket_metadata(self):
        layout = self.layout
        handler = self.ticket.handler
        group = handler.group or self.ticket.group
        created = layout.to_timezone(self.ticket.created, layout.timezone)
        created = layout.format_date(created, 'datetime')

        # Ticket meta info
        if hasattr(self.ticket, 'reference_group'):
            subject = self.ticket.reference_group(layout.request)
        else:
            subject = self.ticket.title

        submitter = ticket_submitter(self.ticket)
        ticket_state = self.translate(TICKET_STATES[self.ticket.state])
        owner = self.ticket.user.username if self.ticket.user_id else ''

        def seconds(time):
            return self.layout.format_seconds(time) if time else ''

        data = [
            [_("Subject"), subject],
            [_("Submitter"), submitter],
            [_("State"), ticket_state],
            [_("Group"), group],
            [_("Owner"), owner],
            [_("Created"), created],
            [_("Reaction Time"), seconds(self.ticket.reaction_time)],
            [_("Process Time"), seconds(self.ticket.process_time)],
        ]

        # In case of imported events..
        event_source = handler.data.get('source')
        if event_source and self.layout.request.is_manager:
            data.append([self.translate(_("Event Source")), event_source])

        self.table(data, 'even')

    def ticket_payment(self):
        price = self.ticket.handler.payment
        if not price:
            return
        state = self.translate(PAYMENT_STATES[price.state])
        # credit card
        self.h2(_('Payment'))
        amount = f'{self.layout.format_number(price.net_amount)}'
        self.table([
            [_('Total Amount'), f'{amount} {price.currency}'],
            [_('State'), state],
            [_('Source'), self.translate(PAYMENT_SOURCES[price.source])],
            [_('Fee'), f'{self.layout.format_number(price.fee)}'],
        ], 'even')

    def p_markup(self, text, style=None):
        super().p_markup(self.translate(text), style)

    def ticket_timeline(self, msg_feed):
        """Will parse the timeline from view_messages_feed """
        if not msg_feed or not msg_feed['messages']:
            return

        tables = {}
        for msg in reversed(msg_feed['messages']):
            table = tables.setdefault(msg['date'], [])

            row = self.extract_feed_info(msg['html'])
            table.append(row)

        for date_, data in tables.items():
            self.h4(date_)
            self.table(data, 'even', first_bold=False)

    @staticmethod
    def extract_feed_info(html):
        """ Must be able to parse templates message_{message.type}.pt and
        return the useful data in cleaned form.
        """
        if not html or html == '<p></p>':
            return

        # Remove unwanted markup
        tags = ['p', 'br', 'strong', 'b', 'em', 'li', 'ol', 'ul', 'li']
        ticket_summary_tags = ['dl', 'dt', 'dd', 'h2', 'div']
        tags += ticket_summary_tags

        attributes = {}
        filters = [whitespace_filter]
        attributes['div'] = 'class'

        cleaner = Cleaner(
            tags=tags,
            attributes=attributes,
            strip=True,
            filters=filters
        )
        html = cleaner.clean(html)
        tree = etree.parse(StringIO(html), etree.HTMLParser())
        data = []

        for el in tree.find('body'):
            if el.tag == 'div':
                class_ = el.attrib['class']
                if class_ == 'timestamp':
                    data = [TicketPdf.inner_html(el), None]
                if class_ == 'text':
                    data[1] = TicketPdf.inner_html(el)
        return data

    @classmethod
    def from_ticket(cls, request, ticket):
        """
        Creates a PDF representation of the ticket. It is sensible to the
        templates used to render the message feed and the summary of the ticket
        coming from ticket handler. With this approach, snapshotted
        summaries are supported.
        """
        result = BytesIO()
        handler = ticket.handler
        layout = TicketLayout(ticket, request)
        pdf = cls(
            result,
            title=ticket.number,
            created=f"{date.today():%d.%m.%Y}",
            link_color='#00538c',
            underline_links=True,
            author=request.host_url,
            ticket=ticket,
            translations=request.app.translations,
            locale=request.locale,
            layout=layout,
            qr_payload=request.link(
                ticket, name=request.is_manager and None or 'status')
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )
        pdf.h(f'{request.translate(_("Ticket"))} {ticket.number}')
        pdf.spacer()

        deleted_message = None
        if handler.deleted:
            summary = ticket.snapshot.get('summary')
            deleted_message = _("The record behind this ticket was removed. "
                                "The following information is a snapshot "
                                "kept for future reference.")
        else:
            summary = handler.get_summary(request)

        pdf.ticket_metadata()

        pdf.h1(_('Summary'))
        if deleted_message:
            pdf.p(pdf.translate(deleted_message))
            pdf.spacer()
        pdf.ticket_summary(summary)
        pdf.ticket_payment()

        # If used for the user instead of the manager...
        messages = MessageCollection(
            request.session,
            channel_id=ticket.number
        )
        if not request.is_manager:
            messages.type = request.app.settings.org.public_ticket_messages

        pdf.h1(request.translate(_("Timeline")))
        pdf.ticket_timeline(view_messages_feed(messages, request))

        pdf.generate()
        result.seek(0)
        return result
