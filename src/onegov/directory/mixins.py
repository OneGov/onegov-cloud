from sedate import to_timezone, standardize_date
from onegov.core.orm.mixins import content_property


class PublicationMixin:
    """
    Defines publication relevant information including timezone.
    Dates are stored unaware of timezone and not converted.
    Concerning forms, this mixin is working with DateTimeField or
    DateTimeLocalField. """

    timezone = content_property(default='Europe/Zurich')
    publication_start = content_property()
    publication_end = content_property()

    @property
    def utc_publication_start(self):
        return standardize_date(self.publication_start, self.timezone)

    @property
    def utc_publication_end(self):
        return standardize_date(self.publication_start, self.timezone)


class TimezonePublicationMixin:
    """Concerning forms, this mixin is working with TimezoneDateTimeField.
    Dates are stored the same way as UTCDateTime type decorator does.
    """

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
        value = self.content.get('publication_end')
        if value:
            value = standardize_date(value, timezone='UTC')
        return value

    @publication_end.setter
    def publication_end(self, value):
        if value is not None:
            value = to_timezone(value, 'UTC').replace(tzinfo=None)
            self.content['publication_end'] = value
