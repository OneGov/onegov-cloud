import socket

from attr import attrs, attrib
from cached_property import cached_property
from contextlib import suppress
from ldap3 import Connection, Server, NONE, RESTARTABLE
from ldap3.core.exceptions import LDAPCommunicationError
from time import sleep


def auto_retry(fn, max_tries=5, pause=0.1):
    """ Retries the decorated function if a LDAP connection error occurs, up
    to a given set of retries, using linear backoff.

    """
    tried = 0

    def retry(self, *args, **kwargs):
        nonlocal tried

        try:
            return fn(self, *args, **kwargs)
        except (LDAPCommunicationError, socket.error):
            tried += 1

            if tried >= max_tries:
                raise

            sleep(tried * 0.1)

            with suppress(ValueError):
                self.try_configuration()

            return retry(self, *args, **kwargs)

    return retry


@attrs()
class LDAPClient():

    # The URL of the LDAP server
    url: str = attrib()

    # The username for the LDAP connection
    username: str = attrib()

    # The password for the LDAP connection
    password: str = attrib()

    @property
    def base_dn(self):
        """ Extracts the distinguished name from the username. """

        name = self.username.lower()

        if 'dc=' in name:
            return 'dc=' + name.split(",dc=", 1)[-1]

        return ''

    @cached_property
    def connection(self):
        """ Returns the read-only connection to the LDAP server.

        Calling this property is not enough to ensure that the connection is
        possible. You should use :meth:`try_configuration` for that.

        """
        return Connection(
            server=Server(self.url, get_info=NONE),
            read_only=True,
            auto_bind=False,
            client_strategy=RESTARTABLE,
        )

    def try_configuration(self):
        """ Verifies the connection to the LDAP server. """

        # disconnect if necessary
        with suppress(LDAPCommunicationError, socket.error):
            self.connection.unbind()

        # clear cache
        del self.__dict__['connection']

        # reconnect
        if not self.connection.rebind(self.username, self.password):
            raise ValueError(f"Failed to connect to {self.url}")

    @auto_retry
    def search(self, query, attributes=()):
        """ Runs an LDAP query against the server and returns a dictionary
        with the distinguished name as key and the given attributes as values
        (also a dict).

        """
        self.connection.search(self.base_dn, query, attributes=attributes)

        return {
            entry.entry_dn: entry.entry_attributes_as_dict
            for entry in self.connection.entries
        }

    @auto_retry
    def compare(self, name, attribute, value):
        """ Returns true if given user's attribute has the expected value.

        :param name:
            The distinguished name (DN) of the LDAP user.

        :param attribute:
            The attribute to query.

        :param value:
            The value to compare to.

        The method returns True if the given value is found on the user.

        This is most notably used for password checks. For example::

            client.compare('cn=admin', 'userPassword', 'hunter2')

        """

        return self.connection.compare(name, attribute, value)
