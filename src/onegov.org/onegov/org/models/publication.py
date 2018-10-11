import sedate

from datetime import datetime
from onegov.core.collection import GenericCollection
from onegov.file import File
from sqlalchemy import and_, text


class PublicationCollection(GenericCollection):

    def __init__(self, session, year=None):
        super().__init__(session)
        self.year = year

    @property
    def model_class(self):
        return File

    def query(self):
        query = super().query().filter_by(published=True, signed=True).filter(
            text("reference->>'content_type' = :content_type").bindparams(
                content_type='application/pdf'
            )
        )

        if self.year:
            s = sedate.replace_timezone(datetime(self.year, 1, 1), 'UTC')
            e = sedate.replace_timezone(datetime(self.year + 1, 1, 1), 'UTC')

            query = query.filter(and_(s <= File.created, File.created < e))

        return query

    def for_year(self, year):
        return self.__class__(self.session, year)

    def first_year(self, timezone):
        query = self.for_year(None).query()\
            .with_entities(File.created)\
            .order_by(File.created)

        first_record = query.first()

        if first_record:
            return sedate.to_timezone(first_record.created, timezone).year
