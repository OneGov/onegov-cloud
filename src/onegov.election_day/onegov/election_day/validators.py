import phonenumbers

from onegov.election_day import _
from wtforms import ValidationError


class ValidPhoneNumber(object):
    """ Makes sure the given input is valid phone number.

    Expects an :class:`wtforms.StringField` instance.

    """

    message = _(
        "Not a valid phone number."
    )

    def __call__(self, form, field):
        if field.data:
            try:
                number = phonenumbers.parse(field.data, 'CH')
            except Exception:
                raise ValidationError(self.message)

            valid = (
                phonenumbers.is_valid_number(number) and
                phonenumbers.is_possible_number(number)
            )
            if not valid:
                raise ValidationError(self.message)
