from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import TypeDecorator, TEXT
import json


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
