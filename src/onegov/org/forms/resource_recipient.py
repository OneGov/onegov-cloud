from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from onegov.reservation import Resource, ResourceCollection
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import BooleanField
from wtforms.validators import InputRequired, Email


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


WEEKDAYS = (
    ("MO", _("Mo")),
    ("TU", _("Tu")),
    ("WE", _("We")),
    ("TH", _("Th")),
    ("FR", _("Fr")),
    ("SA", _("Sa")),
    ("SU", _("Su")),
)


class ResourceRecipientForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    name = StringField(
        label=_("Name"),
        fieldset="Empfänger",
        description="Peter Muster",
        validators=[InputRequired()]
    )

    address = EmailField(
        label=_("E-Mail"),
        fieldset="Empfänger",
        description="peter.muster@example.org",
        validators=[InputRequired(), Email()]
    )

    new_reservations = BooleanField(
        label=_("New Reservations"),
        fieldset=_("Notifications *"),
        description=_("For each new reservation, a notification will be sent "
                      "to the above recipient."),
    )

    daily_reservations = BooleanField(
        label=_("Daily Reservations"),
        fieldset=_("Notifications *"),
        description=_("On each day selected below, a notification with the "
                      "day's reservations will be sent to the recipient above "
                      "at 06:00."),
    )

    internal_notes = BooleanField(
        label=_("Internal Notes"),
        fieldset=_("Notifications *"),
        description=_("Each time a new note is added to the ticket for a "
                      "reservation, a notification is sent to the recipient "
                      "above."),
    )

    rejected_reservations = BooleanField(
        label=_("Rejected Reservations"),
        fieldset=_("Notifications *"),
        description=_("If a reservation is cancelled, a notification will "
                      "be sent to the above recipient."),
    )

    send_on = MultiCheckboxField(
        label=_("Send on"),
        fieldset="Tage und Ressourcen",
        choices=WEEKDAYS,
        default=[key for key, value in WEEKDAYS],
        validators=[InputRequired()],
        depends_on=('daily_reservations', 'y'),
        render_kw={'prefix_label': False, 'class_': 'oneline-checkboxes'}
    )

    resources = MultiCheckboxField(
        label=_("Resources"),
        fieldset="Tage und Ressourcen",
        validators=[InputRequired()],
        choices=None
    )

    def validate(self) -> bool:  # type:ignore[override]
        result = super().validate()
        if not (
            self.new_reservations.data
            or self.daily_reservations.data
            or self.internal_notes.data
            or self.rejected_reservations.data
        ):
            assert isinstance(self.daily_reservations.errors, list)
            self.daily_reservations.errors.append(
                _("Please add at least one notification.")
            )
            result = False
        return result

    def on_request(self) -> None:
        self.populate_resources()

    def populate_resources(self) -> None:
        q = ResourceCollection(self.request.app.libres_context).query()
        q = q.order_by(Resource.group, Resource.name)
        q = q.with_entities(Resource.group, Resource.title, Resource.id)

        default_group = self.request.translate(_("General"))

        self.resources.choices = [
            (r.id.hex, f'{r.group or default_group} - {r.title}')
            for r in q
        ]
