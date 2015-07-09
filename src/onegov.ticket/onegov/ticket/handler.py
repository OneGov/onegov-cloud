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

    def __init__(self, ticket, handler_data):
        self.ticket = ticket
        self.data = handler_data

    def refresh(self):
        """ Updates the current ticket with the latest data from the handler.
        """

        self.ticket.title = self.title
        self.ticket.group = self.group
        self.ticket.handler_data = self.data

    @property
    def id(self):
        """ Returns the id of the handler. Not supposed to ever change! """
        raise NotImplementedError

    @property
    def shortcode(self):
        """ Returns the three characters long shortcode of the handler added
        in front of the ticket number. Not supposed to ever change!

        Examples for good shortcodes:

            FRM
            ONS
            RES
            EVT

        """
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
        """

        raise NotImplementedError
