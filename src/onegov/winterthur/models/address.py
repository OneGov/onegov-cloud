from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.mixins import TimestampMixin
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Self


class WinterthurAddress(Base, TimestampMixin):

    __tablename__ = 'winterthur_addresses'

    #: the adress id
    id: Mapped[int] = mapped_column(primary_key=True)

    #: the street
    street_id: Mapped[int]
    street: Mapped[str]

    #: the house
    house_number: Mapped[int]
    house_extra: Mapped[str | None]

    #: the place
    zipcode: Mapped[int]
    zipcode_extra: Mapped[int | None]

    place: Mapped[str]

    #: the district
    district: Mapped[str]

    #: the neighbourhood
    neighbourhood: Mapped[str]

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
