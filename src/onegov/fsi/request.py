from __future__ import annotations

from functools import cached_property
from onegov.town6.request import TownRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import CourseAttendee
    from uuid import UUID


class FsiRequest(TownRequest):

    @cached_property
    def attendee(self) -> CourseAttendee | None:
        return (
            # FIXME: backref across module boundaries
            self.current_user.attendee  # type:ignore[attr-defined]
            if self.current_user else None
        )

    @cached_property
    def attendee_id(self) -> UUID | None:
        return self.attendee.id if self.attendee else None

    @cached_property
    def is_editor(self) -> bool:
        return (
            self.current_user
            and self.current_user.role == 'editor' or False
        )

    @cached_property
    def is_member(self) -> bool:
        return (
            self.current_user
            and self.current_user.role == 'member' or False
        )
