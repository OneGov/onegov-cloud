from attr import attrs, attrib
from cached_property import cached_property
from ldap3 import Connection, Server, NONE


@attrs()
class LDAPClient():

    # The URL of the LDAP server
    url: str = attrib()

    # The username for the LDAP connection
    username: str = attrib()

    # The password for the LDAP connection
    password: str = attrib()

    @url.validator
    def is_secure(self, attribute, value):
        """ Asserts that LDAP can only be connect to via TLS. """

        if not value.startswith('ldaps://'):
            raise ValueError(f"Invalid url: {value}, must start with ldaps://")

    @property
    def base_dn(self):
        """ Extracts the distinguished name from the username. """

        return 'dc=' + self.username.lower().split(",dc=", 1)[-1]

    @cached_property
    def connection(self):
        """ Returns the read-only connection to the LDAP server.

        Calling this property is not enough to ensure that the connection is
        possible. You should use :meth:`try_configuration` for that.

        """
        return Connection(
            server=Server(self.url, get_info=NONE),
            read_only=True,
            auto_bind=False
        )

    def try_configuration(self):
        """ Verifies the connection to the LDAP server. """

        if not self.connection.rebind(self.username, self.password):
            raise ValueError(f"Failed to connect to {self.url}")

    def search(self, query, attributes={}):
        """ Runs an LDAP query against the server and returns a dictionary
        with the distinguished name as key and the given attributes as values
        (also a dict).

        """
        self.connection.search(self.base_dn, query, attributes=attributes)

        return {
            entry.entry_dn: entry.entry_attributes_as_dict
            for entry in self.connection.entries
        }
