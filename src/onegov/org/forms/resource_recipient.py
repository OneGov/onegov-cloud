from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from onegov.reservation import Resource, ResourceCollection
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import BooleanField
from wtforms.validators import InputRequired, Email


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
        description=("Bei jeder neuen Reservation wird eine Benachrichtigung "
                     "an den obenstehendes Empfänger gesendet."),
    )

    daily_reservations = BooleanField(
        label=_("Daily Reservations"),
        fieldset=_("Notifications *"),
        description=("An jedem unten ausgewählten Tag wird um 06:00 eine "
                     "Benachrichtigung mit den Reservationen des Tages an den "
                     "obenstehenden Empfänger gesendet."),
    )

    internal_notes = BooleanField(
        label=_("Internal Notes"),
        fieldset=_("Notifications *"),
        description=("Bei jeder neuen Notiz auf dem Ticket zu einer "
                     "Reservation wird eine Benachrichtigung an den "
                     "obenstehenden Empfänger gesendet."),
    )

    rejected_reservations = BooleanField(
        label=_("Rejected Reservations"),
        fieldset=_("Notifications *"),
        description=("Bei der Stornierung einer Reservation wird eine "
                     "Benachrichtigung an den obenstehenden Empfänger "
                     "gesendet."),
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

    def validate(self):
        result = super().validate()
        if not (
            self.new_reservations.data
            or self.daily_reservations.data
            or self.internal_notes.data
            or self.rejected_reservations.data
        ):
            self.daily_reservations.errors.append(
                _("Please add at least one notification.")
            )
            result = False
        return result

    def on_request(self):
        self.populate_resources()

    def populate_resources(self):
        q = ResourceCollection(self.request.app.libres_context).query()
        q = q.order_by(Resource.group, Resource.name)
        q = q.with_entities(Resource.group, Resource.title, Resource.id)

        default_group = self.request.translate(_("General"))

        self.resources.choices = tuple(
            (r.id.hex, "{group} - {title}".format(
                group=r.group or default_group,
                title=r.title
            ))
            for r in q
        )
