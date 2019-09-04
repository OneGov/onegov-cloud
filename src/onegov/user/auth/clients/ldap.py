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

    @property
    def base_dn(self):
        return 'dc=' + self.username.lower().split(",dc=", 1)[-1]

    @url.validator
    def is_secure(self, attribute, value):
        if not value.startswith('ldaps://'):
            raise ValueError(f"Invalid url: {value}, must start with ldaps://")

    @cached_property
    def server(self):
        return Server(self.url, get_info=NONE)

    @cached_property
    def connection(self):
        return Connection(server=self.server, read_only=True, auto_bind=False)

    def try_configuration(self):
        if not self.connection.rebind(self.username, self.password):
            raise ValueError(f"Failed to connect to {self.url}")

    def search(self, query, attributes={}):
        self.connection.search(self.base_dn, query, attributes=attributes)

        return {
            entry.entry_dn: entry.entry_attributes_as_dict
            for entry in self.connection.entries
        }
