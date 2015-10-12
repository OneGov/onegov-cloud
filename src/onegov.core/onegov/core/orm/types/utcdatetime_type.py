from sedate import standardize_date, to_timezone
from sqlalchemy import types


class UTCDateTime(types.TypeDecorator):
    """ Stores dates as UTC.

    Internally, they are stored as timezone naive, because Postgres takes
    the local timezone into account when working with timezones. Values taken
    and values returned are forced to be timezone-aware though.

    """

    impl = types.DateTime

    def __init__(self):
        super().__init__(timezone=False)

    def process_bind_param(self, value, engine):
        if value is not None:
            return to_timezone(value, 'UTC').replace(tzinfo=None)

    def process_result_value(self, value, engine):
        if value is not None:
            return standardize_date(value, timezone='UTC')
