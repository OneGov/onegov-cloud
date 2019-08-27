from sqlalchemy.dialects.postgresql import UUID as BaseUUID


class UUID(BaseUUID):
    """ The UUID type used throughout OneGov. The base is always the UUID type
    defined by SQLAlchemy for Postgres, but we change the default to actually
    handle the values as uuid.UUID values.

    Another approach could be the following:

    `<https://github.com/seantis/libres/blob/master/\
    libres/db/models/types/uuid_type.py>`_

    We can switch to this any time.

    """

    def __init__(self, as_uuid=True):
        super().__init__(as_uuid=as_uuid)
