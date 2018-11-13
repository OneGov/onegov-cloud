from onegov.agency import _
from onegov.form import Form
from wtforms import StringField
from wtforms import validators
from onegov.form.fields import ChosenSelectField
from onegov.agency.collections import ExtendedPersonCollection


class MembershipForm(Form):
    """ Form to edit memberships of an organization. """

    title = StringField(
        label=_("Title"),
        validators=[
            validators.InputRequired()
        ],
    )

    person_id = ChosenSelectField(
        label=_("Person"),
        choices=[],
        validators=[
            validators.InputRequired()
        ]
    )

    since = StringField(
        label=_("Since"),
    )

    note = StringField(
        label=_("Note"),
    )

    addition = StringField(
        label=_("Addition"),
    )

    prefix = StringField(
        label=_("Prefix"),
    )

    def on_request(self):
        self.request.include('common')
        self.request.include('chosen')
        self.person_id.choices = [
            (str(p.id), p.title)
            for p in ExtendedPersonCollection(self.request.session).query()
        ]
