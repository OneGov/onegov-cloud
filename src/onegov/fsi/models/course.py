from uuid import uuid4

from sqlalchemy import Column, Text

from onegov.core.orm import Base
from onegov.core.orm.types import UUID


class Course(Base):
    __tablename__ = 'fsi_courses'

    id = Column(UUID, primary_key=True, default=uuid4)

    name = Column(Text, nullable=False, unique=True)
    # Long description
    description = Column(Text, nullable=False)
