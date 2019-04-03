from cached_property import cached_property
from onegov.chat import Message
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.core.utils import paragraphify, linkify
from onegov.event import Event
from onegov.org import _
from onegov.org.utils import hashtag_elements
from onegov.ticket import Ticket, TicketCollection
from sqlalchemy.orm import object_session

# 👉 when adding new ticket messages be sure to evaluate if they should
# be added to the ticket status page through the org.public_ticket_messages
# setting


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
    def create(cls, ticket, request, text=None, owner=None, **extra_meta):
        meta = {
            'id': ticket.id.hex,
            'handler_code': ticket.handler_code,
            'group': ticket.group
        }
        meta.update(extra_meta)

        # force a change of the ticket to make sure that it gets reindexed
        ticket.force_update()

        # the owner can be forced to a specific value
        owner = owner or request.current_username or ticket.ticket_email

        return cls.bound_messages(request.session).add(
            channel_id=ticket.number,
            owner=owner,
            text=text,
            meta=meta
        )


class TicketNote(Message, TicketMessageMixin):
    __mapper_args__ = {
        'polymorphic_identity': 'ticket_note'
    }

    @classmethod
    def create(cls, ticket, request, text, file=None, owner=None):
        note = super().create(ticket, request, text=text, owner=owner)
        note.file = file

        return note

    def formatted_text(self, layout):
        return hashtag_elements(
            layout.request, paragraphify(linkify(self.text)))

    def links(self, layout):
        yield Link(_("Edit"), layout.request.link(self, 'edit'))
        yield Link(
            _("Delete"), layout.csrf_protected_url(layout.request.link(self)),
            traits=(
                Confirm(
                    _("Do you really want to delete this note?"),
                    _("This cannot be undone."),
                    _("Delete Note"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method="DELETE",
                    redirect_after=layout.request.link(self.ticket)
                )
            ))


class TicketChatMessage(Message, TicketMessageMixin):
    """ Chat messages sent between the person in charge of the ticket and
    the submitter of the ticket.

    Paramters of note:

    - origin: 'external' or 'internal', to differentiate between the
              messages sent from the organisation to someone outside or
              from someone outside to someone inside.

    - notify: only relevant for messages originating from 'internal' - if the
              last sent message with origin 'internal' has this flag, a
              notification is sent to the owner of that message, whenever
              a new external reply comes in.

    """

    __mapper_args__ = {
        'polymorphic_identity': 'ticket_chat'
    }

    @classmethod
    def create(cls, ticket, request, text, owner, origin,
               notify=False, recipient=None):

        return super().create(
            ticket, request, text=text, owner=owner, origin=origin,
            notify=notify, recipient=recipient)

    def formatted_text(self, layout):
        return self.text and hashtag_elements(
            layout.request, paragraphify(linkify(self.text))) or ''

    @property
    def subtype(self):
        return self.meta.get('origin', None)


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
