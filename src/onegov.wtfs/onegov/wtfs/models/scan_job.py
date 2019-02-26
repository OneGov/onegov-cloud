from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.user import UserGroup
from onegov.wtfs import _
from onegov.wtfs.models.municipality import Municipality
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Sequence
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


def _sum(*values):
    return sum([(value or 0) for value in values]) or None


class ScanJob(Base, TimestampMixin, ContentMixin):
    """ A tax form scan job date. """

    __tablename__ = 'wtfs_scan_jobs'

    #: the id of the db record (only relevant internally)
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The group that owns the scan job.
    group_id = Column(UUID, ForeignKey(UserGroup.id), nullable=False)
    group = relationship(
        UserGroup,
        backref=backref(
            'scan_jobs',
            lazy='dynamic',
            order_by='ScanJob.dispatch_date'
        )
    )

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

    @property
    def dispatch_tax_forms(self):
        return _sum(
            self.dispatch_tax_forms_current_year,
            self.dispatch_tax_forms_last_year,
            self.dispatch_tax_forms_older
        )

    dispatch_single_documents = Column(Integer, nullable=True)
    dispatch_cantonal_tax_office = Column(Integer, nullable=True)
    dispatch_cantonal_scan_center = Column(Integer, nullable=True)

    return_date = Column(Date, nullable=True)
    return_note = Column(Text, nullable=True)
    return_boxes = Column(Integer, nullable=True)

    return_scanned_tax_forms_current_year = Column(Integer, nullable=True)
    return_scanned_tax_forms_last_year = Column(Integer, nullable=True)
    return_scanned_tax_forms_older = Column(Integer, nullable=True)

    @property
    def return_scanned_tax_forms(self):
        return _sum(
            self.return_scanned_tax_forms_current_year,
            self.return_scanned_tax_forms_last_year,
            self.return_scanned_tax_forms_older
        )

    return_scanned_single_documents = Column(Integer, nullable=True)

    return_unscanned_tax_forms_current_year = Column(Integer, nullable=True)
    return_unscanned_tax_forms_last_year = Column(Integer, nullable=True)
    return_unscanned_tax_forms_older = Column(Integer, nullable=True)

    @property
    def return_unscanned_tax_forms(self):
        return _sum(
            self.return_unscanned_tax_forms_current_year,
            self.return_unscanned_tax_forms_last_year,
            self.return_unscanned_tax_forms_older
        )

    return_unscanned_single_documents = Column(Integer, nullable=True)

    @property
    def return_tax_forms_current_year(self):
        return _sum(
            self.return_scanned_tax_forms_current_year,
            -(self.return_unscanned_tax_forms_current_year or 0)
        )

    @property
    def return_tax_forms_last_year(self):
        return _sum(
            self.return_scanned_tax_forms_last_year,
            -(self.return_unscanned_tax_forms_last_year or 0)
        )

    @property
    def return_tax_forms_older(self):
        return _sum(
            self.return_scanned_tax_forms_older,
            -(self.return_unscanned_tax_forms_older or 0)
        )

    @property
    def return_tax_forms(self):
        return _sum(
            self.return_scanned_tax_forms,
            -(self.return_unscanned_tax_forms or 0)
        )

    @property
    def return_single_documents(self):
        return _sum(
            self.return_scanned_single_documents,
            -(self.return_unscanned_single_documents or 0)
        )

    @property
    def title(self):
        return _(
            "Scan job no. ${number}",
            mapping={'number': self.delivery_number}
        )
