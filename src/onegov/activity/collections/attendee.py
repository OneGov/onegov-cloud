from __future__ import annotations

from onegov.activity.models import Attendee
from onegov.core.collection import GenericCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.user import User
    from sqlalchemy.orm import Query


class AttendeeCollection(GenericCollection[Attendee]):

    @property
    def model_class(self) -> type[Attendee]:
        return Attendee

    def by_user(self, user: User) -> Query[Attendee]:
        return self.query().filter(self.model_class.username == user.username)

    def by_username(self, username: str) -> Query[Attendee]:
        return self.query().filter(self.model_class.username == username)

    def add(  # type:ignore[override]
        self,
        user: User,
        name: str,
        birth_date: date,
        gender: str | None,
        notes: str | None = None,
        swisspass: str | None = None,
        differing_address: bool = False,
        address: str | None = None,
        zip_code: str | None = None,
        place: str | None = None,
        political_municipality: str | None = None
    ) -> Attendee:

        return super().add(
            username=user.username,
            name=name,
            birth_date=birth_date,
            gender=gender,
            notes=notes,
            swisspass=swisspass,
            differing_address=differing_address,
            address=address,
            zip_code=zip_code,
            place=place,
            political_municipality=political_municipality
        )
