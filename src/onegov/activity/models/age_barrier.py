from datetime import datetime
from dateutil import relativedelta


class AgeBarrier(object):
    """ Holds various age barrier approaches available to the period. """

    registry = {}

    def __init_subclass__(cls, name, **kwargs):
        assert name not in cls.registry
        cls.registry[name] = cls

        super().__init_subclass__(**kwargs)

    @classmethod
    def from_name(cls, name, *args, **kwargs):
        return cls.registry[name](*args, **kwargs)

    def is_too_young(self, birth_date, start_date, min_age):
        raise NotImplementedError()

    def is_too_old(self, birth_date, start_date, max_age):
        raise NotImplementedError()


class ExactAgeBarrier(AgeBarrier, name='exact'):
    """ Checks the age by exact date.

    The attendee can be 1 year too old (otherwise, the day the attendee
    is a day older than the max age, he'll be rejected - in other word
    the min age is exclusive, the max age is inclusive).

    """

    def age(self, birth_date, start_date):
        """ Calculates the age at the given date. """

        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()

        return relativedelta.relativedelta(start_date, birth_date).years

    def is_too_young(self, birth_date, start_date, min_age):
        return self.age(birth_date, start_date) < min_age

    def is_too_old(self, birth_date, start_date, max_age):
        return self.age(birth_date, start_date) > max_age


class YearAgeBarrier(AgeBarrier, name='year'):
    """ Checks the age by using the year of the start_date and the age.

    In German, we would say this is by "Jahrgang".

    """

    def is_too_young(self, birth_date, start_date, min_age):
        return (start_date.year - birth_date.year) < min_age

    def is_too_old(self, birth_date, start_date, max_age):
        return (start_date.year - birth_date.year) > max_age
