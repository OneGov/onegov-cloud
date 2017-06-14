from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from uuid import uuid4


class UploadToken(Base, TimestampMixin):
    """ Stores tokens for uploading using the REST interface. """

    __tablename__ = 'upload_tokens'

    #: Identifies the token
    id = Column(UUID, primary_key=True, default=uuid4)

    #: The token
    token = Column(UUID, unique=True, default=uuid4)
