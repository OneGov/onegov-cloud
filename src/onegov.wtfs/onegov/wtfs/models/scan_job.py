from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.wtfs import _
from onegov.wtfs.models.municipality import Municipality
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import Sequence
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


class ScanJob(Base, TimestampMixin, ContentMixin):
    """ A tax form scan job date. """

    __tablename__ = 'wtfs_scan_jobs'

    #: the id of the db record (only relevant internally)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The municipality that owns the scan job.
    municipality_id = Column(UUID, ForeignKey(Municipality.id), nullable=False)
    municipality = relationship(
        Municipality,
        backref=backref(
            'scan_jobs',
            lazy='dynamic',
            order_by='ScanJob.dispatch_date'
        )
    )

    #: The scan job type.
    type = Column(
        Enum('normal', 'express', name='wtfs_scan_job_type'),
        nullable=False
    )

    #: The delivery number.
    delivery_number = Column(
        Integer,
        Sequence('delivery_number_seq', metadata=Base.metadata),
        nullable=False
    )

    dispatch_date = Column(Date, nullable=False)
    dispatch_note = Column(Text, nullable=True)
    dispatch_boxes = Column(Integer, nullable=True)

    dispatch_tax_forms_current_year = Column(Integer, nullable=True)
    dispatch_tax_forms_last_year = Column(Integer, nullable=True)
    dispatch_tax_forms_older = Column(Integer, nullable=True)

    @hybrid_property
    def dispatch_tax_forms(self):
        return (
            (self.dispatch_tax_forms_current_year or 0)
            + (self.dispatch_tax_forms_last_year or 0)
            + (self.dispatch_tax_forms_older or 0)
        ) or None

    @dispatch_tax_forms.expression
    def dispatch_tax_forms(cls):
        return (
            func.coalesce(cls.dispatch_tax_forms_current_year, 0)
            + func.coalesce(cls.dispatch_tax_forms_last_year, 0)
            + func.coalesce(cls.dispatch_tax_forms_older, 0)
        )

    dispatch_single_documents = Column(Integer, nullable=True)
    dispatch_cantonal_tax_office = Column(Integer, nullable=True)
    dispatch_cantonal_scan_center = Column(Integer, nullable=True)

    return_date = Column(Date, nullable=True)
    return_note = Column(Text, nullable=True)
    return_boxes = Column(Integer, nullable=True)

    return_tax_forms_current_year = Column(Integer, nullable=True)
    return_tax_forms_last_year = Column(Integer, nullable=True)
    return_tax_forms_older = Column(Integer, nullable=True)

    @hybrid_property
    def return_tax_forms(self):
        return (
            (self.return_tax_forms_current_year or 0)
            + (self.return_tax_forms_last_year or 0)
            + (self.return_tax_forms_older or 0)
        ) or None

    @return_tax_forms.expression
    def return_tax_forms(cls):
        return (
            func.coalesce(cls.return_tax_forms_current_year, 0)
            + func.coalesce(cls.return_tax_forms_last_year, 0)
            + func.coalesce(cls.return_tax_forms_older, 0)
        )

    return_single_documents = Column(Integer, nullable=True)

    return_unscanned_tax_forms_current_year = Column(Integer, nullable=True)
    return_unscanned_tax_forms_last_year = Column(Integer, nullable=True)
    return_unscanned_tax_forms_older = Column(Integer, nullable=True)

    @hybrid_property
    def return_unscanned_tax_forms(self):
        return (
            (self.return_unscanned_tax_forms_current_year or 0)
            + (self.return_unscanned_tax_forms_last_year or 0)
            + (self.return_unscanned_tax_forms_older or 0)
        ) or None

    @return_unscanned_tax_forms.expression
    def return_unscanned_tax_forms(cls):
        return (
            func.coalesce(cls.return_unscanned_tax_forms_current_year, 0)
            + func.coalesce(cls.return_unscanned_tax_forms_last_year, 0)
            + func.coalesce(cls.return_unscanned_tax_forms_older, 0)
        )

    return_unscanned_single_documents = Column(Integer, nullable=True)

    @hybrid_property
    def return_scanned_tax_forms_current_year(self):
        return (
            (self.return_tax_forms_current_year or 0)
            - (self.return_unscanned_tax_forms_current_year or 0)
        ) or None

    @return_scanned_tax_forms_current_year.expression
    def return_scanned_tax_forms_current_year(cls):
        return (
            func.coalesce(cls.return_tax_forms_current_year, 0)
            - func.coalesce(cls.return_unscanned_tax_forms_current_year, 0)
        )

    @hybrid_property
    def return_scanned_tax_forms_last_year(self):
        return (
            (self.return_tax_forms_last_year or 0)
            - (self.return_unscanned_tax_forms_last_year or 0)
        ) or None

    @return_scanned_tax_forms_last_year.expression
    def return_scanned_tax_forms_last_year(cls):
        return (
            func.coalesce(cls.return_tax_forms_last_year, 0)
            - func.coalesce(cls.return_unscanned_tax_forms_last_year, 0)
        )

    @hybrid_property
    def return_scanned_tax_forms_older(self):
        return (
            (self.return_tax_forms_older or 0)
            - (self.return_unscanned_tax_forms_older or 0)
        ) or None

    @return_scanned_tax_forms_older.expression
    def return_scanned_tax_forms_older(cls):
        return (
            func.coalesce(cls.return_tax_forms_older, 0)
            - func.coalesce(cls.return_unscanned_tax_forms_older, 0)
        )

    @hybrid_property
    def return_scanned_tax_forms(self):
        return (
            (self.return_tax_forms or 0)
            - (self.return_unscanned_tax_forms or 0)
        ) or None

    @return_scanned_tax_forms.expression
    def return_scanned_tax_forms(cls):
        return (
            func.coalesce(cls.return_tax_forms, 0)
            - func.coalesce(cls.return_unscanned_tax_forms, 0)
        )

    @hybrid_property
    def return_scanned_single_documents(self):
        return (
            (self.return_single_documents or 0)
            - (self.return_unscanned_single_documents or 0)
        ) or None

    @return_scanned_single_documents.expression
    def return_scanned_single_documents(cls):
        return (
            func.coalesce(cls.return_single_documents, 0)
            - func.coalesce(cls.return_unscanned_single_documents, 0)
        )

    @property
    def title(self):
        return _(
            "Scan job no. ${number}",
            mapping={'number': self.delivery_number}
        )
