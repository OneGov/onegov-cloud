from wtforms.validators import InputRequired
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi import _


class FsiReservationForm(Form):

    attendee_id = ChosenSelectField(
        label=_("Attendee"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    course_event_id = ChosenSelectField(
        label=_("Course Event"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        attendee = self.model.attendee
        event = self.model.course_event
        attendee_collection = CourseAttendeeCollection(
            self.request.session, external_only=self.model.external_only)
        event_collection = CourseEventCollection(
            self.request.session, upcoming_only=True)

        def _repr(attendee):
            return f'{str(attendee)} - {attendee.email}'

        if attendee:
            self.attendee_id.choices = ((str(attendee.id), _repr(attendee)),)
        else:
            self.attendee_id.choices = list(
                (str(a.id), _repr(a)) for a in attendee_collection.query()
            )
            if not self.attendee_id.choices:
                self.attendee_id.choices.append(('', _('None')))

        if event:
            self.course_event_id.choices = ((str(event.id), event.name),)
        else:
            self.course_event_id.choices = list(
                (str(a.id), a.name) for a in event_collection.query()
            )

