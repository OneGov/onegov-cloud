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

    dayly_reservations = BooleanField(
        label=_("Tägliche Belegung"),
        fieldset="Benachrichtigung",
        description=("Jeden Tag um 06:00 wird eine Benachrichtigung mit den "
                     "Reservationen des Tages an die obenstehende Adresse "
                     "gesendet."),
    )

    new_reservations = BooleanField(
        label=_("Neue Reservationen"),
        fieldset="Benachrichtigung",
        description=("Bei jeder neuen Reservation wird eine Benachrichtigung "
                     "an die obenstehende Adresse gesendet."),
    )

    send_on = MultiCheckboxField(
        label=_("Send on"),
        fieldset="Tage und Ressourcen",
        choices=WEEKDAYS,
        default=[key for key, value in WEEKDAYS],
        validators=[InputRequired()],
        render_kw={'prefix_label': False, 'class_': 'oneline-checkboxes'}
    )

    resources = MultiCheckboxField(
        label=_("Resources"),
        fieldset="Tage und Ressourcen",
        validators=[InputRequired()],
        choices=None
    )

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
