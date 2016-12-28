from onegov.activity import Activity
from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import Period
from onegov.feriennet import _
from onegov.feriennet.layout import DefaultLayout
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.user import User, UserCollection
from sqlalchemy import distinct
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
        render_kw={'rows': 12}
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

    occasion = MultiCheckboxField(
        label=_("Occasion"),
        choices=None,
        depends_on=('send_to', 'by_occasion')
    )

    def on_request(self):
        self.populate_occasion()
        self.limit_send_to_choices_for_organisers()

    @property
    def has_choices(self):
        return self.request.is_admin or bool(self.occasion.choices)

    @property
    def recipients(self):
        if self.request.is_organiser_only and self.send_to.data == 'by_role':
            return None

        if self.send_to.data == 'by_role':
            return self.recipients_by_role(self.roles.data)

        elif self.send_to.data == 'by_occasion':
            return self.recipients_by_occasion(self.occasion.data)

        else:
            raise NotImplementedError

    def limit_send_to_choices_for_organisers(self):
        if self.request.is_organiser_only:
            assert len(self.send_to.choices) == 2
            self.send_to.choices = [
                ('by_occasion', _(
                    "All attendees of a given occasion in the current period"
                ))
            ]
            self.send_to.data = 'by_occasion'

    def recipients_by_role(self, roles):
        if not roles:
            return None

        users = UserCollection(self.request.app.session())

        q = users.by_roles(*roles)
        q = q.with_entities(User.username)

        return list(u.username for u in q)

    def recipients_by_occasion(self, occasions):
        bookings = BookingCollection(self.request.app.session())

        q = bookings.query()
        q = q.join(Period)
        q = q.filter(Booking.occasion_id.in_(occasions))
        q = q.filter(Booking.state == 'accepted')
        q = q.filter(Period.active == True)
        q = q.filter(Period.confirmed == True)
        q = q.with_entities(distinct(Booking.username).label('username'))

        return list(b.username for b in q)

    def populate_occasion(self):
        q = OccasionCollection(self.request.app.session()).query()
        q = q.join(Activity)
        q = q.join(Period)
        q = q.filter(Period.active == True)
        q = q.order_by(Activity.name, Occasion.start)

        if self.request.is_organiser_only:
            q = q.filter(Activity.username == self.request.current_username)

        layout = DefaultLayout(self.model, self.request)

        def choice(occasion):
            return occasion.id.hex, self.request.translate(_(
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

        assert not self.occasion.choices
        self.occasion.choices = tuple(choice(o) for o in q)
