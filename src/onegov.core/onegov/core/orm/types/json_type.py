# We use our own custom json implementation. In the libres library we made this
# configurable. Since onegov.core is a framework we don't do that though, we
# want all onegov.core applications with the same framework version to be able
# to read each others json.
#
# Therefore we use a common denominator kind of json encoder/decoder.
from onegov.core import custom_json as json

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import TypeDecorator, TEXT


class JSON(TypeDecorator):
    """ A JSON type for postgres that's backwards compatible with Postgres 9.1.

    In the future this will be replaced by JSON (or JSONB) though that requires
    that we require a later Postgres release. It would also mean that all
    json types have to be migrated.

    This type is associated with Sqlalchemy's MutableDict, so changes made to
    the dict are reflected in the database.

    See http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/mutable.html

    """

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)

        return value


MutableDict.associate_with(JSON)
