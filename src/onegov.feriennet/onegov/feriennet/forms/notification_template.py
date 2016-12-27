from onegov.activity import Activity, Occasion, OccasionCollection, Period
from onegov.feriennet import _
from onegov.feriennet.layout import DefaultLayout
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from wtforms.fields import StringField, TextAreaField, RadioField
from wtforms.validators import InputRequired


class NotificationTemplateForm(Form):

    subject = StringField(
        label=_("Subject"),
        validators=[InputRequired()]
    )

    text = TextAreaField(
        label=_("Message"),
        validators=[InputRequired()],
        render_kw={'rows': 8}
    )


class NotificationTemplateSendForm(Form):

    send_to = RadioField(
        label=_("Send to"),
        choices=[
            ('by_role', _("All users of a given role")),
            ('by_occasion', _(
                "All attendees of a given occasion in the current period"
            )),
        ],
        default='by_role'
    )

    roles = MultiCheckboxField(
        label=_("Role"),
        choices=[
            ('admin', _("Administrators")),
            ('editor', _("Organisers")),
            ('member', _("Members"))
        ],
        depends_on=('send_to', 'by_role')
    )

    occasions = MultiCheckboxField(
        label=_("Occasion"),
        choices=None,
        depends_on=('send_to', 'by_occasion')
    )

    def on_request(self):
        self.populate_occasions()
        self.limit_send_to_choices_for_organisers()

    @property
    def has_recipients(self):
        return self.request.is_admin or bool(self.occasions.choices)

    def limit_send_to_choices_for_organisers(self):
        if self.request.is_organiser_only:
            assert len(self.send_to.choices) == 2
            self.send_to.choices = [
                ('by_occasion', _(
                    "All attendees of a given occasion in the current period"
                ))
            ]
            self.send_to.data = 'by_occasion'

    def populate_occasions(self):
        q = OccasionCollection(self.request.app.session()).query()
        q = q.join(Activity)
        q = q.join(Period)
        q = q.filter(Period.active == True)
        q = q.order_by(Activity.name, Occasion.start)

        if self.request.is_organiser_only:
            q = q.filter(Activity.username == self.request.current_username)

        layout = DefaultLayout(self.model, self.request)

        def choice(occasion):
            return str(occasion.id), self.request.translate(_(
                '${title} <small>${date}, ${count} Attendees</small>',
                mapping={
                    'title': occasion.activity.title,
                    'date': layout.format_datetime_range(
                        occasion.localized_start,
                        occasion.localized_end
                    ),
                    'count': occasion.attendee_count
                }
            ))

        assert not self.occasions.choices
        self.occasions.choices = tuple(choice(o) for o in q)
