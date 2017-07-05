from onegov.chat import Message
from onegov.core.templates import render_template
from onegov.event import Event
from onegov.ticket import Ticket


class TemplateRenderedMessage(Message):

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


class TicketBasedMessage(TemplateRenderedMessage):

    def link(self, request):
        return request.class_link(Ticket, {
            'id': self.meta['id'],
            'handler_code': self.meta['handler_code'],
        })

    @classmethod
    def create(cls, ticket, request, **extra_meta):
        meta = {
            'id': ticket.id.hex,
            'handler_code': ticket.handler_code,
            'group': ticket.group
        }
        meta.update(extra_meta)

        return cls.bound_messages(request).add(
            channel_id=ticket.number,
            owner=request.current_username or ticket.ticket_email,
            meta=meta
        )


class TicketMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'ticket'
    }

    @classmethod
    def create(cls, ticket, request, change):
        return super().create(ticket, request, change=change)


class ReservationMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'reservation'
    }

    @classmethod
    def create(cls, reservations, ticket, request, change):
        return super().create(ticket, request, change=change, reservations=[
            r.id for r in reservations
        ])


class EventMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'event'
    }

    @classmethod
    def create(cls, event, ticket, request, change):
        return super().create(
            ticket, request, change=change, event_name=event.name)

    def event_link(self, request):
        return request.class_link(Event, {'name': self.meta['event_name']})


class PaymentMessage(TicketBasedMessage):

    __mapper_args__ = {
        'polymorphic_identity': 'payment'
    }

    @classmethod
    def create(cls, payment, ticket, request, change):
        return super().create(
            ticket, request,
            change=change,
            payment_id=payment.id.hex,
            amount=float(payment.amount),
            currency=payment.currency
        )
