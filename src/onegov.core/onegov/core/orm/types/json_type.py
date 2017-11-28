# We use our own custom json implementation. In the libres library we made this
# configurable. Since onegov.core is a framework we don't do that though, we
# want all onegov.core applications with the same framework version to be able
# to read each others json.
#
# Therefore we use a common denominator kind of json encoder/decoder.
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB


class JSON(TypeDecorator):
    """ A JSONB based type that coerces None's to empty dictionaries.

    That is, this JSONB column does not have NULL values, it only has
    falsy values (an empty dict).

    """

    impl = JSONB

    def process_bind_param(self, value, dialect):
        if value is None:
            return {}

        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return {}

        return value


MutableDict.associate_with(JSON)
