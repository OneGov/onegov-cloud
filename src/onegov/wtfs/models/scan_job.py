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
from sqlalchemy import Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import date


class ScanJob(Base, TimestampMixin, ContentMixin):
    """ A tax form scan job date. """

    __tablename__ = 'wtfs_scan_jobs'

    #: the id of the db record (only relevant internally)
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The if of the municipality that owns the scan job.
    municipality_id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(Municipality.id),
        nullable=False
    )

    #: The municipality that owns the scan job.
    municipality: 'relationship[Municipality]' = relationship(
        Municipality,
        back_populates='scan_jobs'
    )

    #: The scan job type.
    type: 'Column[Literal["normal", "express"]]' = Column(
        Enum('normal', 'express', name='wtfs_scan_job_type'),  # type:ignore
        nullable=False
    )

    #: The delivery number.
    delivery_number: 'Column[int]' = Column(
        Integer,
        nullable=False
    )

    dispatch_date: 'Column[date]' = Column(Date, nullable=False)
    dispatch_note: 'Column[str | None]' = Column(Text, nullable=True)
    dispatch_boxes: 'Column[int | None]' = Column(Integer, nullable=True)

    dispatch_tax_forms_current_year: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    dispatch_tax_forms_last_year: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    dispatch_tax_forms_older: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )

    if TYPE_CHECKING:
        dispatch_tax_forms: Column[int | None]
    else:
        @hybrid_property
        def dispatch_tax_forms(self) -> int | None:
            return (
                (self.dispatch_tax_forms_current_year or 0)
                + (self.dispatch_tax_forms_last_year or 0)
                + (self.dispatch_tax_forms_older or 0)
            ) or None

        @dispatch_tax_forms.expression  # type:ignore[no-redef]
        def dispatch_tax_forms(cls):
            return (
                func.coalesce(cls.dispatch_tax_forms_current_year, 0)
                + func.coalesce(cls.dispatch_tax_forms_last_year, 0)
                + func.coalesce(cls.dispatch_tax_forms_older, 0)
            )

    dispatch_single_documents: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    dispatch_cantonal_tax_office: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    dispatch_cantonal_scan_center: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )

    return_date: 'Column[date | None]' = Column(Date, nullable=True)
    return_note: 'Column[str | None]' = Column(Text, nullable=True)
    return_boxes: 'Column[int | None]' = Column(Integer, nullable=True)

    return_tax_forms_current_year: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    return_tax_forms_last_year: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    return_tax_forms_older: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )

    if TYPE_CHECKING:
        return_tax_forms: Column[int | None]
    else:
        @hybrid_property
        def return_tax_forms(self) -> int | None:
            return (
                (self.return_tax_forms_current_year or 0)
                + (self.return_tax_forms_last_year or 0)
                + (self.return_tax_forms_older or 0)
            ) or None

        @return_tax_forms.expression  # type:ignore[no-redef]
        def return_tax_forms(cls):
            return (
                func.coalesce(cls.return_tax_forms_current_year, 0)
                + func.coalesce(cls.return_tax_forms_last_year, 0)
                + func.coalesce(cls.return_tax_forms_older, 0)
            )

    return_single_documents: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )

    return_unscanned_tax_forms_current_year: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    return_unscanned_tax_forms_last_year: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )
    return_unscanned_tax_forms_older: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )

    if TYPE_CHECKING:
        return_unscanned_tax_forms: Column[int | None]
    else:
        @hybrid_property
        def return_unscanned_tax_forms(self) -> int | None:
            return (
                (self.return_unscanned_tax_forms_current_year or 0)
                + (self.return_unscanned_tax_forms_last_year or 0)
                + (self.return_unscanned_tax_forms_older or 0)
            ) or None

        @return_unscanned_tax_forms.expression  # type:ignore[no-redef]
        def return_unscanned_tax_forms(cls):
            return (
                func.coalesce(cls.return_unscanned_tax_forms_current_year, 0)
                + func.coalesce(cls.return_unscanned_tax_forms_last_year, 0)
                + func.coalesce(cls.return_unscanned_tax_forms_older, 0)
            )

    return_unscanned_single_documents: 'Column[int | None]' = Column(
        Integer,
        nullable=True
    )

    if TYPE_CHECKING:
        return_scanned_tax_forms_current_year: Column[int | None]
        return_scanned_tax_forms_last_year: Column[int | None]
        return_scanned_tax_forms_older: Column[int | None]
        return_scanned_tax_forms: Column[int | None]
        return_scanned_single_documents: Column[int | None]
    else:
        @hybrid_property
        def return_scanned_tax_forms_current_year(self) -> int | None:
            return (
                (self.return_tax_forms_current_year or 0)
                - (self.return_unscanned_tax_forms_current_year or 0)
            ) or None

        @return_scanned_tax_forms_current_year.expression  # type:ignore
        def return_scanned_tax_forms_current_year(cls):
            return (
                func.coalesce(cls.return_tax_forms_current_year, 0)
                - func.coalesce(cls.return_unscanned_tax_forms_current_year, 0)
            )

        @hybrid_property
        def return_scanned_tax_forms_last_year(self) -> int | None:
            return (
                (self.return_tax_forms_last_year or 0)
                - (self.return_unscanned_tax_forms_last_year or 0)
            ) or None

        @return_scanned_tax_forms_last_year.expression  # type:ignore[no-redef]
        def return_scanned_tax_forms_last_year(cls):
            return (
                func.coalesce(cls.return_tax_forms_last_year, 0)
                - func.coalesce(cls.return_unscanned_tax_forms_last_year, 0)
            )

        @hybrid_property
        def return_scanned_tax_forms_older(self) -> int | None:
            return (
                (self.return_tax_forms_older or 0)
                - (self.return_unscanned_tax_forms_older or 0)
            ) or None

        @return_scanned_tax_forms_older.expression  # type:ignore[no-redef]
        def return_scanned_tax_forms_older(cls):
            return (
                func.coalesce(cls.return_tax_forms_older, 0)
                - func.coalesce(cls.return_unscanned_tax_forms_older, 0)
            )

        @hybrid_property
        def return_scanned_tax_forms(self) -> int | None:
            return (
                (self.return_tax_forms or 0)
                - (self.return_unscanned_tax_forms or 0)
            ) or None

        @return_scanned_tax_forms.expression  # type:ignore[no-redef]
        def return_scanned_tax_forms(cls):
            return (
                func.coalesce(cls.return_tax_forms, 0)
                - func.coalesce(cls.return_unscanned_tax_forms, 0)
            )

        @hybrid_property
        def return_scanned_single_documents(self) -> int | None:
            return (
                (self.return_single_documents or 0)
                - (self.return_unscanned_single_documents or 0)
            ) or None

        @return_scanned_single_documents.expression  # type:ignore[no-redef]
        def return_scanned_single_documents(cls):
            return (
                func.coalesce(cls.return_single_documents, 0)
                - func.coalesce(cls.return_unscanned_single_documents, 0)
            )

    @property
    def title(self) -> str:
        return _(
            'Scan job no. ${number}',
            mapping={'number': self.delivery_number}
        )
