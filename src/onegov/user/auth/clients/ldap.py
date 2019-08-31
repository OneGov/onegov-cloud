from attr import attrs, attrib
from cached_property import cached_property
from ldap3 import Connection


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
        if not value.startswith('ldaps://'):
            raise ValueError(f"Invalid url: {value}, must start with ldaps://")

    @cached_property
    def connection(self):
        return Connection(server=self.url)

    def try_configuration(self):
        if not self.connection.rebind(self.username, self.password):
            raise ValueError(f"Failed to connect to {self.url}")
