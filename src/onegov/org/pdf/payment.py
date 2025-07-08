from __future__ import annotations

from io import BytesIO
from onegov.core.utils import module_path
from onegov.org.pdf.ticket import TicketPdf
from onegov.ticket import Ticket, TicketCollection
from pdfdocument.document import PDFDocument


from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from onegov.ticket import Ticket
    from onegov.pay import Payment


def ticket_by_link(
    tickets: TicketCollection,
    link: Any
) -> Ticket | None:

    # FIXME: We should probably do isinstance checks so type checkers
    #        can understand that a Reservation has a token and a
    #        FormSubmission has a id...
    if link.__tablename__ == 'reservations':
        return tickets.by_handler_id(link.token.hex)
    elif link.__tablename__ == 'submissions':
        return tickets.by_handler_id(link.id.hex)
    return None


class PaymentsPdf(PDFDocument):
    """Creates a PDF with multiple payment tickets combined."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.font_path = module_path('onegov.org', 'fonts')

    @classmethod
    def from_payments(
        cls, payments: list[Payment], session: Any, title: str = 'Payments'
    ) -> bytes:
        """Creates a PDF with all tickets from the given payments."""
        output = BytesIO()
        pdf = cls(output)
        pdf.init_report()

        tickets = TicketCollection(session)

        # Get all tickets from payments
        for payment in payments:
            for link in payment.links:
                ticket = ticket_by_link(tickets, link)
                if ticket:
                    # Add a page break between tickets
                    if pdf.story and pdf.story[-1] != pdf.pagebreak():
                        pdf.story.append(pdf.pagebreak())

                    # Generate ticket PDF content
                    ticket_pdf = TicketPdf.from_ticket(
                        ticket=ticket,
                        with_content=True,
                        exclude_payment_code=True,
                        title=title,
                    )

                    # Extract content from ticket PDF and add to our PDF
                    ticket_io = BytesIO(ticket_pdf)
                    pdf.append_pdf(ticket_io)

        pdf.generate()
        result = output.getvalue()
        output.close()

        return result
