from sedate import to_timezone, standardize_date
from onegov.core.orm.mixins import content_property


class PublicationMixin:
    """Mixin that stores and retrieves dates the same way as
    UTCDateTime type decorator. Always use it with timezone aware datetimes """

    # publication_start = meta_property()
    # publication_end = meta_property()
    timezone = content_property(default='Europe/Zurich')

    @property
    def publication_start(self):
        value = self.content.get('publication_start')
        if value:
            value = standardize_date(value, timezone='UTC')
        return value

    @publication_start.setter
    def publication_start(self, value):
        if value is not None:
            value = to_timezone(value, 'UTC').replace(tzinfo=None)
            self.content['publication_start'] = value

    @property
    def publication_end(self):
        value = self.content.get('publication_start')
        if value:
            value = standardize_date(value, timezone='UTC')
        return value

    @publication_end.setter
    def publication_end(self, value):
        if value is not None:
            value = to_timezone(value, 'UTC').replace(tzinfo=None)
            self.content['publication_end'] = value
