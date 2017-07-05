from onegov.chat import Message, MessageCollection
from onegov.core.templates import render_template
from onegov.event import Event
from onegov.ticket import Ticket


class MacroRenderedMessage(Message):

    def get(self, request, owner, layout):
        return render_template(
            template='message_{}'.format(self.type),
            request=request,
            content={
                'layout': layout,
                'model': self,
                'owner': owner
            },
            suppress_global_variables=True
        )


class TicketBasedMessage(MacroRenderedMessage):

    def link(self, request):
        return request.class_link(Ticket, {
            'id': self.meta['id'],
            'handler_code': self.meta['handler_code'],
        })


class TicketChangeMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'ticket_change'
    }

    @classmethod
    def create(cls, ticket, request, change):
        messages = MessageCollection(
            request.app.session(), type='ticket_change')

        return messages.add(
            channel_id=ticket.number,
            owner=request.current_username or ticket.ticket_email,
            meta={
                'id': ticket.id.hex,
                'handler_code': ticket.handler_code,
                'change': change,
                'group': ticket.group
            }
        )


class ReservationDecisionMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'reservation_decision'
    }

    @classmethod
    def create(cls, reservations, ticket, request, change):
        messages = MessageCollection(
            request.app.session(), type='reservation_decision')

        return messages.add(
            channel_id=ticket.number,
            owner=request.current_username or ticket.ticket_email,
            meta={
                'id': ticket.id.hex,
                'handler_code': ticket.handler_code,
                'change': change,
                'group': ticket.group,
                'reservations': [r.id for r in reservations]
            }
        )


class EventPublicationMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'event_publication'
    }

    @classmethod
    def create(cls, event, ticket, request, change):
        messages = MessageCollection(
            request.app.session(), type='event_publication')

        return messages.add(
            channel_id=ticket.number,
            owner=request.current_username or ticket.ticket_email,
            meta={
                'id': ticket.id.hex,
                'handler_code': ticket.handler_code,
                'group': ticket.group,
                'change': change,
                'event_name': event.name
            }
        )

    def event_link(self, request):
        return request.class_link(Event, {'name': self.meta['event_name']})


class PaymentChangeMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'payment_change'
    }

    @classmethod
    def create(cls, payment, ticket, request, change):
        messages = MessageCollection(
            request.app.session(), type='payment_change')

        return messages.add(
            channel_id=ticket.number,
            owner=request.current_username or ticket.ticket_email,
            meta={
                'id': ticket.id.hex,
                'handler_code': ticket.handler_code,
                'group': ticket.group,
                'change': change,
                'payment_id': payment.id.hex,
                'amount': float(payment.amount),
                'currency': payment.currency
            }
        )
