from cached_property import cached_property
from onegov.chat import Message
from onegov.core.utils import linkify
from onegov.event import Event
from onegov.org import _
from onegov.org.new_elements import Link, Confirm, Intercooler
from onegov.ticket import Ticket, TicketCollection
from sqlalchemy.orm import object_session


class TicketMessageMixin(object):

    def link(self, request):
        return request.class_link(Ticket, {
            'id': self.meta['id'],
            'handler_code': self.meta['handler_code'],
        })

    @cached_property
    def ticket(self):
        return TicketCollection(object_session(self)).by_id(
            self.meta['id'],
            self.meta['handler_code']
        )

    @classmethod
    def create(cls, ticket, request, **extra_meta):
        meta = {
            'id': ticket.id.hex,
            'handler_code': ticket.handler_code,
            'group': ticket.group
        }
        meta.update(extra_meta)

        # force a change of the ticket to make sure that it gets reindexed
        ticket.force_update()

        return cls.bound_messages(request.session).add(
            channel_id=ticket.number,
            owner=request.current_username or ticket.ticket_email,
            meta=meta
        )


class TicketNote(Message, TicketMessageMixin):
    __mapper_args__ = {
        'polymorphic_identity': 'ticket_note'
    }

    @classmethod
    def create(cls, ticket, request, text, file=None):
        note = super().create(ticket, request)
        note.text = text
        note.file = file

        return note

    @property
    def formatted_text(self):
        return linkify(self.text).replace('\n', '<br>')

    def links(self, layout):
        yield Link(_("Edit"), layout.request.link(self, 'edit'))
        yield Link(
            _("Delete"), layout.csrf_protected_url(layout.request.link(self)),
            traits=(
                Confirm(
                    _("Do you really want to delete this note?"),
                    _("This cannot be undone."),
                    _("Delete Note")
                ),
                Intercooler(
                    request_method="DELETE",
                    redirect_after=layout.request.link(self.ticket)
                )
            ))


class TicketMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'ticket'
    }

    @classmethod
    def create(cls, ticket, request, change):
        return super().create(ticket, request, change=change)


class ReservationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'reservation'
    }

    @classmethod
    def create(cls, reservations, ticket, request, change):
        return super().create(ticket, request, change=change, reservations=[
            r.id for r in reservations
        ])


class SubmissionMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'submission'
    }

    @classmethod
    def create(cls, ticket, request, change):
        return super().create(ticket, request, change=change)


class EventMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'event'
    }

    @classmethod
    def create(cls, event, ticket, request, change):
        return super().create(
            ticket, request, change=change, event_name=event.name)

    def event_link(self, request):
        return request.class_link(Event, {'name': self.meta['event_name']})


class PaymentMessage(Message, TicketMessageMixin):

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


class DirectoryMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'directory'
    }

    @classmethod
    def create(cls, directory, ticket, request, action):
        return super().create(
            ticket, request,
            directory_id=directory.id.hex,
            action=action
        )
