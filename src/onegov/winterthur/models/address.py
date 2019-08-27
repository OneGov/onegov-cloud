from onegov.core.orm import Base
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text


class WinterthurAddress(Base):

    __tablename__ = 'winterthur_addresses'

    #: the adress id
    id = Column(Integer, nullable=False, primary_key=True)

    #: the street
    street_id = Column(Integer, nullable=False)
    street = Column(Text, nullable=False)

    #: the house
    house_number = Column(Integer, nullable=False)
    house_extra = Column(Text, nullable=True)

    #: the place
    zipcode = Column(Integer, nullable=False)
    zipcode_extra = Column(Integer, nullable=True)

    place = Column(Text, nullable=False)

    #: the district
    district = Column(Text, nullable=False)

    #: the neighbourhood
    neighbourhood = Column(Text, nullable=False)

    @classmethod
    def as_addressless(cls, street_id, street):
        return cls(
            street_id=street_id,
            street=street,
            house_number=-1,
            zipcode=-1,
            place="",
            district="",
            neighbourhood="",
        )

    @property
    def is_addressless(self):
        return self.house_number == -1

    @property
    def title(self):
        if self.is_addressless:
            return self.street
        else:
            return f"{self.street} {self.house_number}{self.house_extra}"
