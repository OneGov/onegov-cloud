from __future__ import annotations

from decimal import Decimal
from onegov.ticket.errors import DuplicateHandlerError
from sqlalchemy.orm import object_session


from typing import Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from markupsafe import Markup
    from onegov.core.request import CoreRequest
    from onegov.pay import InvoiceItemMeta, Payment
    from onegov.ticket.models import Ticket
    from sqlalchemy.orm import Query, Session
    from typing import TypeAlias
    from uuid import UUID

    _LinkOrCallback: TypeAlias = tuple[str, str] | Callable[[CoreRequest], str]

_H = TypeVar('_H', bound='Handler')
_Q = TypeVar('_Q', bound='Query[Any]')


class Handler:
    """ Defines a generic handler, responsible for a subset of the tickets.

    onegov.ticket is meant to be a rather generic bucket of tickets, to which
    varying modules submit tickets with varying content and different
    actionables.

    Each module wanting to submit tickets needs to implement a handler with
    a unique id and a unique short code. The short code is added in front of
    the ticket number.

    Tickets submitted to the database are shown in a list, without handler
    involvement. When a ticket is displayed, the handler is called with
    whatever data the handler supplied during ticket submission.

    The handler then uses the handler data to access whatever data it needs
    to display a summary as well as links to certain actions (possibly a link
    to the original item, links that change the state of the ticket as well
    as the data associated with the handler, etc.).

    """

    def __init__(
        self,
        ticket: Ticket,
        handler_id: UUID | str,
        handler_data: dict[str, Any]
    ):
        self.ticket = ticket
        self.id = handler_id
        self.data = handler_data

    @property
    def session(self) -> Session:
        return object_session(self.ticket)

    def refresh(self) -> None:
        """ Updates the current ticket with the latest data from the handler.
        """

        if self.deleted:
            return

        if self.ticket.title != self.title:
            self.ticket.title = self.title

        if self.ticket.subtitle != self.subtitle:
            self.ticket.subtitle = self.subtitle

        if self.ticket.group != self.group:
            # FIXME: Deal with a group of None, since some handlers
            #        appear to return None for group
            self.ticket.group = self.group  # type: ignore[assignment]

        if self.ticket.handler_id != str(self.id):
            self.ticket.handler_id = str(self.id)

        if self.ticket.handler_data != self.data:
            self.ticket.handler_data = self.data

        if self.ticket.ticket_email != self.email:
            self.ticket.ticket_email = self.email

        payment = self.payment
        payment_id = payment.id if payment else None
        if self.ticket.payment_id != payment_id:
            self.ticket.payment_id = payment_id

    def invoice_items(self, request: CoreRequest) -> list[InvoiceItemMeta]:
        """ Returns the generated invoice items based on the current state
        of the ticket.
        """
        raise NotImplementedError

    def refresh_invoice_items(self, request: CoreRequest) -> None:
        """ Updates the invoice items with the latest data from the handler.
        """
        raise NotImplementedError

    def refreshing_invoice_is_safe(self, request: CoreRequest) -> bool:
        """ Whether or not is safe to refresh the invoice.

        Currently we disallow changing the total amount for a
        non-manual non-open payment.
        """
        payment = self.payment
        if payment is None:
            return True

        if payment.state == 'open' and payment.source == 'manual':
            return True

        invoice = self.ticket.invoice
        if invoice is None:
            expected = Decimal('0')
        else:
            expected = invoice.total_excluding_manual_entries

        # if the total doesn't change, we're fine
        # TODO: What if we have a manual discount that results in a negative
        #       total and we end up with a new non-positive total? Either way
        #       we don't get a change in payment, so it should be fine. But
        #       it also seems a little bit fragile to allow this.
        # FIXME: circular import
        from onegov.pay import InvoiceItemMeta
        return InvoiceItemMeta.total(self.invoice_items(request)) == expected

    @property
    def email(self) -> str | None:
        """ Returns the email address behind the ticket request. """
        raise NotImplementedError

    @property
    def email_changeable(self) -> bool:
        """ Returns whether or not the email address behind the ticket request
        may be changed.
        """
        return False

    def change_email(self, email: str) -> None:
        """ Handles the logic for changing the email.

        Every handler is tied to a different set of objects, which may or
        may not store the email redundantly. So they all need to be changed
        in order for data to remain consistent.

        This method is only expected to work for handlers that return ``True``
        for `email_changeable`.
        """
        raise NotImplementedError

    @property
    def submitter_name(self) -> str | None:
        """ Returns the name of the submitter """
        return None

    @property
    def submitter_address(self) -> str | None:
        """ Returns the address of the submitter """
        return None

    @property
    def submitter_phone(self) -> str | None:
        """ Returns the phone of the submitter """
        return None

    @property
    def title(self) -> str:
        """ Returns the title of the ticket. If this title may change over
        time, the handler must call :meth:`self.refresh` when there's a change.

        """
        raise NotImplementedError

    @property
    def subtitle(self) -> str | None:
        """ Returns the subtitle of the ticket. If this title may change over
        time, the handler must call :meth:`self.refresh` when there's a change.

        """
        raise NotImplementedError

    @property
    def group(self) -> str | None:
        """ Returns the group of the ticket. If this group may change over
        time, the handler must call :meth:`self.refresh` when there's a change.

        """
        raise NotImplementedError

    @property
    def deleted(self) -> bool:
        """ Returns true if the underlying model was deleted. It is best to
        never let that happen, as we want tickets to stay around forever.

        However, this can make sense in certain scenarios. Note that if
        you do delete your underlying model, make sure to call
        :meth:`onegov.ticket.models.Ticket.create_snapshot` beforehand!

        """

        raise NotImplementedError

    @property
    def extra_data(self) -> Sequence[str]:
        """ An array of string values which are indexed in elasticsearch when
        the ticket is stored there.

        """

        return ()

    @property
    def payment(self) -> Payment | None:
        """ An optional link to a onegov.pay payment record. """

        return None

    @property
    def show_vat(self) -> bool:
        """ Whether or not to show VAT for this ticket. """
        return False

    @property
    def undecided(self) -> bool:
        """ Returns true if there has been no decision about the subject
        of this handler.

        For example, if a reservation ticket has been accepted, but the
        reservation has been neither confirmed nor cancelled, the ticket
        can be seen as undecided.

        This is an optional flag that may be implemented by handlers. If
        a ticket is undecided, the UI might show a special icon and it might
        warn the user if he closes the ticket without making a decision.

        By default, the ticket is assumed to be decided for backwards
        compatibility and for tickets where this does not make sense (a simple
        form submission may not have any way of knowing if there has been
        a decision or not).

        """

        return False

    @property
    def reply_to(self) -> str | None:
        """ An optional email address which will be used as a Reply-To
        in mails instead of any global setting.

        For example for a certain subset of forms you may want replies
        to end up with the department in charge of those specific forms
        instead of a global bucket.

        """

        return None

    @classmethod
    def handle_extra_parameters(
        cls,
        session: Session,
        query: _Q,
        extra_parameters: dict[str, Any]
    ) -> _Q:
        """ Takes a dictionary of extra parameters and uses it to optionally
        modifiy the query used for the collection.

        Use this to add handler-defined custom filters with extra query
        parameters. Only called if the collection is already limited to the
        given handler. If all handlers are shown in the collection, this
        method is not called.

        If no extra paramaters were given, this method is *not* called.

        Returns the modified or unmodified query.

        """
        return query

    def get_summary(self, request: CoreRequest) -> Markup:
        """ Returns the summary of the current ticket as a html string. """

        raise NotImplementedError

    def get_links(self, request: CoreRequest) -> Sequence[_LinkOrCallback]:
        """ Returns the links associated with the current ticket in the
        following format::

            [
                ('Link Title', 'http://link'),
                ('Link Title 2', 'http://link2'),
            ]

        If the links are not tuples, but callables, they will be called with
        the request which should return the rendered link.
        """

        raise NotImplementedError

    @property
    def ticket_deletable(self) -> bool:
        if self.deleted:
            return True
        if self.ticket.state != 'archived':
            return False
        if self.payment:
            # For now we do not handle this case since payment might be
            # needed for exports
            return False
        if self.undecided:
            return False
        return True

    def prepare_delete_ticket(self) -> None:
        """The handler knows best what to do when a ticket is called for
        deletion. """
        assert self.ticket_deletable


class HandlerRegistry:

    _reserved_handler_codes = {'ALL'}
    registry: dict[str, type[Handler]]

    def __init__(self) -> None:
        self.registry = {}

    def get(self, handler_code: str) -> type[Handler]:
        """ Returns the handler registration for the given id. If the id
        does not exist, a KeyError is raised.

        """
        return self.registry[handler_code]

    def register(
        self,
        handler_code: str,
        handler_class: type[Handler]
    ) -> None:
        """ Registers a handler.

        :handler_code:
            Three characters long shortcode of the handler added in front of
            the ticket number. Must be globally unique and must not change!

            Examples for good handler_codes::

                FRM
                ONS
                RES
                EVT

        :handler_class:
            A handler class inheriting from :class:`Handler`.

        """

        assert len(handler_code) == 3
        assert handler_code == handler_code.upper()
        assert handler_code not in self._reserved_handler_codes

        if handler_code in self.registry:
            raise DuplicateHandlerError

        self.registry[handler_code] = handler_class

    def registered_handler(
        self,
        handler_code: str
    ) -> Callable[[type[_H]], type[_H]]:
        """ A decorator to register handles.

        Use as followed::

            @handlers.registered_handler('FOO')
            class FooHandler(Handler):
                pass

        """
        def wrapper(handler_class: type[_H]) -> type[_H]:
            self.register(handler_code, handler_class)
            return handler_class
        return wrapper
