from __future__ import annotations


class BookingLimitReached(RuntimeError):
    def __init__(self) -> None:
        super().__init__('The booking limit has been reached')
