from onegov.agency import _
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import ExtendedPerson
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from sqlalchemy import func
from wtforms import StringField
from wtforms import validators


def duplicates(iterable):
    items = set()
    duplicates = set()
    for item in iterable:
        if item in items:
            duplicates.add(item)
        items.add(item)
    return duplicates


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

        ambiguous = duplicates([
            r[0] for r in self.request.session.query(
                func.concat(
                    ExtendedPerson.last_name, ' ', ExtendedPerson.first_name
                )
            )
        ])

        def title(person):
            if person.title in ambiguous:
                info = (
                    person.phone_direct
                    or person.phone
                    or person.email
                    or person.address
                )
                if info:
                    return f"{person.title} ({info})"
                memberships = person.memberships_by_agency
                if memberships:
                    return f"{person.title} ({memberships[0].agency.title})"

            return person.title

        self.person_id.choices = [
            (str(p.id), title(p))
            for p in ExtendedPersonCollection(self.request.session).query()
        ]
