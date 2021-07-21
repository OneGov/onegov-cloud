from sedate import utcnow
from sqlalchemy import Column, case, func, and_, not_
from sqlalchemy.ext.hybrid import hybrid_property
from onegov.core.orm.types import UTCDateTime


class UTCPublicationMixin:

    #: Optional publication dates
    publication_start = Column(UTCDateTime, nullable=True)
    publication_end = Column(UTCDateTime, nullable=True)

    @hybrid_property
    def publication_started(self):
        if not self.publication_start:
            return True
        return self.publication_start <= utcnow()

    @publication_started.expression
    def publication_started(cls):
        return case((
            (
                cls.publication_start == None,
                True
            ),
        ), else_=cls.publication_start <= func.now())

    @hybrid_property
    def publication_ended(self):
        if not self.publication_end:
            return False
        return self.publication_end < utcnow()

    @publication_ended.expression
    def publication_ended(cls):
        return case((
            (
                cls.publication_end == None,
                False
            ),
        ), else_=cls.publication_end < func.now())

    @hybrid_property
    def published(self):
        return self.publication_started and not self.publication_ended

    @published.expression
    def published(cls):
        return and_(cls.publication_started, not_(cls.publication_ended))
