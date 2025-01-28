from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self


class WinterthurAddress(Base, TimestampMixin):

    __tablename__ = 'winterthur_addresses'

    #: the adress id
    id: Column[int] = Column(Integer, nullable=False, primary_key=True)

    #: the street
    street_id: Column[int] = Column(Integer, nullable=False)
    street: Column[str] = Column(Text, nullable=False)

    #: the house
    house_number: Column[int] = Column(Integer, nullable=False)
    house_extra: Column[str | None] = Column(Text, nullable=True)

    #: the place
    zipcode: Column[int] = Column(Integer, nullable=False)
    zipcode_extra: Column[int | None] = Column(Integer, nullable=True)

    place: Column[str] = Column(Text, nullable=False)

    #: the district
    district: Column[str] = Column(Text, nullable=False)

    #: the neighbourhood
    neighbourhood: Column[str] = Column(Text, nullable=False)

    @classmethod
    def as_addressless(cls, street_id: int, street: str) -> Self:
        return cls(
            street_id=street_id,
            street=street,
            house_number=-1,
            zipcode=-1,
            place='',
            district='',
            neighbourhood='',
        )

    @property
    def is_addressless(self) -> bool:
        return self.house_number == -1

    @property
    def title(self) -> str:
        if self.is_addressless:
            return self.street
        else:
            return f'{self.street} {self.house_number}{self.house_extra}'
