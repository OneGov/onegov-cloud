from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import UUID, uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .file import File


class SigningRequest(Base, TimestampMixin):
    """ This keeps track of any requests issued to our configured
    signing services.

    This is mainly useful for billing customers. We already store
    signature metadata on signed files. But we may wish to sign
    generated files that are e.g. attached to an e-mail for attestation
    purposes, which we don't necessarily want to store, since they
    would need to be re-generated and re-signed once things change.

    """

    __tablename__ = 'signing_requests'

    #: the unique identifier of the signing request
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the name of the used signing service
    service_name: Mapped[str]

    #: the request_id returned by the signing service
    request_id: Mapped[str]

    #: the id of the file that was signed in this request
    #: if we stored it and it still exists
    file_id: Mapped[str | None] = mapped_column(ForeignKey(
        'files.id',
        ondelete='SET NULL'
    ))

    file: Mapped[File | None] = relationship(passive_deletes=True)
