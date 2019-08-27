from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.org import _
from wtforms import StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Email
from onegov.reservation import Resource, ResourceCollection


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
        description="Peter Muster",
        validators=[InputRequired()]
    )

    address = EmailField(
        label=_("E-Mail"),
        description="peter.muster@example.org",
        validators=[InputRequired(), Email()]
    )

    send_on = MultiCheckboxField(
        label=_("Send on"),
        choices=WEEKDAYS,
        default=[key for key, value in WEEKDAYS],
        validators=[InputRequired()],
        render_kw={'prefix_label': False, 'class_': 'oneline-checkboxes'}
    )

    resources = MultiCheckboxField(
        label=_("Resources"),
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
