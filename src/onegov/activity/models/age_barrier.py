from __future__ import annotations

from datetime import date, datetime

from dateutil import relativedelta


class AgeBarrier:
    """ Holds various age barrier approaches available to the period. """

    registry: dict[str, type[AgeBarrier]] = {}

    def __init_subclass__(cls, name: str, **kwargs: object):
        assert name not in cls.registry
        cls.registry[name] = cls

        super().__init_subclass__(**kwargs)

    @classmethod
    def from_name(
        cls,
        name: str,
        *args: object,
        **kwargs: object
    ) -> AgeBarrier:
        return cls.registry[name](*args, **kwargs)

    def is_too_young(
        self,
        birth_date: date | datetime,
        start_date: date,
        min_age: int
    ) -> bool:
        raise NotImplementedError()

    def is_too_old(
        self,
        birth_date: date | datetime,
        start_date: date,
        max_age: int
    ) -> bool:
        raise NotImplementedError()


class ExactAgeBarrier(AgeBarrier, name='exact'):
    """ Checks the age by exact date.

    The attendee can be 1 year too old (otherwise, the day the attendee
    is a day older than the max age, he'll be rejected - in other word
    the min age is exclusive, the max age is inclusive).

    """

    def age(self, birth_date: date | datetime, start_date: date) -> int:
        """ Calculates the age at the given date. """

        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()

        return relativedelta.relativedelta(start_date, birth_date).years

    def is_too_young(
        self,
        birth_date: date | datetime,
        start_date: date,
        min_age: int
    ) -> bool:
        return self.age(birth_date, start_date) < min_age

    def is_too_old(
        self,
        birth_date: date | datetime,
        start_date: date,
        max_age: int
    ) -> bool:
        return self.age(birth_date, start_date) > max_age


class YearAgeBarrier(AgeBarrier, name='year'):
    """ Checks the age by using the year of the start_date and the age.

    In German, we would say this is by "Jahrgang".
    The person must be of that age during the year of the start date.

    """

    def is_too_young(
        self,
        birth_date: date | datetime,
        start_date: date,
        min_age: int
    ) -> bool:
        return (birth_date.year + min_age) > start_date.year

    def is_too_old(
        self,
        birth_date: date | datetime,
        start_date: date,
        max_age: int
    ) -> bool:
        return (birth_date.year + max_age + 1) < start_date.year
