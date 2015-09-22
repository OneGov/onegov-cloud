from onegov.ticket.errors import DuplicateHandlerError
from sqlalchemy.orm import object_session


class Handler(object):
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

    def __init__(self, ticket, handler_id, handler_data):
        self.ticket = ticket
        self.id = handler_id
        self.data = handler_data

    @property
    def session(self):
        return object_session(self.ticket)

    def refresh(self):
        """ Updates the current ticket with the latest data from the handler.
        """

        if self.deleted:
            return

        if self.ticket.title != self.title:
            self.ticket.title = self.title

        if self.ticket.group != self.group:
            self.ticket.group = self.group

        if self.ticket.handler_id != self.id:
            self.ticket.handler_id = self.id

        if self.ticket.handler_data != self.data:
            self.ticket.handler_data = self.data

    @property
    def email(self):
        """ Returns the email address behind the ticket request. """
        raise NotImplementedError

    @property
    def title(self):
        """ Returns the title of the ticket. If this title may change over
        time, the handler must call :meth:`self.refresh` when there's a change.

        """
        raise NotImplementedError

    @property
    def group(self):
        """ Returns the group of the ticket. If this group may change over
        time, the handler must call :meth:`self.refresh` when there's a change.

        """
        raise NotImplementedError

    @property
    def deleted(self):
        """ Returns true if the underlying model was deleted. It is best to
        never let that happen, as we want tickets to stay around forever.

        However, this can make sense in certain scenarios. Note that if
        you do delete your underlying model, make sure to call
        :meth:`onegov.ticket.models.Ticket.create_snapshot` beforehand!

        """

        raise NotImplementedError

    @property
    def extra_data(self):
        """ An array of string values which are indexed in elasticsearch when
        the ticket is stored there.

        """

        return tuple()

    @classmethod
    def handle_extra_parameters(self, session, query, extra_parameters):
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

    def get_summary(self, request):
        """ Returns the summary of the current ticket as a html string. """

        raise NotImplementedError

    def get_links(self, request):
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


class HandlerRegistry(object):

    _reserved_handler_codes = {'ALL'}

    def __init__(self):
        self.registry = {}

    def get(self, handler_code):
        """ Returns the handler registration for the given id. If the id
        does not exist, a KeyError is raised.

        """
        return self.registry[handler_code]

    def register(self, handler_code, handler_class):
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

    def registered_handler(self, handler_code):
        """ A decorator to register handles as follows::

        @handlers.registered_handler('FOO')
        class FooHandler(Handler):
            pass

        """
        def wrapper(handler_class):
            self.register(handler_code, handler_class)
            return handler_class
        return wrapper
