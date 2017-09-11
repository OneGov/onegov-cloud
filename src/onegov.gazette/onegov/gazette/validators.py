from wtforms.validators import ValidationError
from onegov.user import User
from onegov.gazette import _


class UniqueUsername(object):
    """ Test if the email is not already used as a username.

    A form field name can be provided to allow a default value.

    """

    def __init__(self, default_field=None):
        self.default_field = default_field

    def __call__(self, form, field):
        query = form.request.app.session().query(User.username)
        query = query.filter(User.username == field.data)
        if self.default_field and hasattr(form, self.default_field):
            query = query.filter(
                User.username != getattr(form, self.default_field).data
            )
        if query.first():
            raise ValidationError(_(
                "A user with this e-mail address already exists."
            ))
