from onegov.activity.models import Attendee
from onegov.core.collection import GenericCollection


class AttendeeCollection(GenericCollection):

    @property
    def model_class(self):
        return Attendee

    def by_user(self, user):
        return self.query().filter(self.model_class.username == user.username)

    def by_username(self, username):
        return self.query().filter(self.model_class.username == username)

    def add(self, user, name, birth_date, gender, notes=None,
            differing_address=False, address=None, zip_code=None, place=None,
            political_municipality=None):

        return super().add(
            username=user.username,
            name=name,
            birth_date=birth_date,
            gender=gender,
            notes=notes,
            differing_address=differing_address,
            address=address,
            zip_code=zip_code,
            place=place,
            political_municipality=political_municipality
        )
