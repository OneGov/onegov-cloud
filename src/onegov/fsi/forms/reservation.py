from wtforms import StringField
from wtforms.validators import InputRequired
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi import _


class AddFsiReservationForm(Form):

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

    dummy_desc = StringField(
        label=_('Placeholder Description (optional)'),
    )

    @property
    def event(self):
        return self.model.course_event

    @property
    def attendee(self):
        return self.model.attendee

    def event_choice(self, event):
        return str(event.id), str(event)

    @staticmethod
    def attendee_choice(attendee):
        return str(attendee.id), f'{str(attendee)}'

    @property
    def event_collection(self):
        return CourseEventCollection(
            self.request.session,
            upcoming_only=True,
            show_hidden=self.request.is_manager
        )

    @property
    def attendee_collection(self):
        return CourseAttendeeCollection(
            self.request.session,
            external_only=self.model.external_only
        )

    @property
    def none_choice(self):
        return '', _('None')

    def get_event_choices(self):

        if self.model.course_event_id:
            return self.event_choice(self.event),

        events = self.event_collection.query()
        if self.model.attendee_id:

            # Filters courses he registered
            events = self.attendee.possible_course_events(
                show_hidden=self.request.is_manager
            )

        return (self.event_choice(e) for e in events)

    def get_attendee_choices(self):

        result = [self.none_choice]
        if self.request.view_name == 'add-placeholder':
            return result

        if self.request.view_name == 'add':

            if self.model.attendee_id:
                return self.attendee_choice(self.attendee),

            attendees = self.attendee_collection.query()
            if self.model.course_event_id:
                attendees = self.event.possible_bookers(
                    external_only=self.model.external_only
                )
            return (self.attendee_choice(a) for a in attendees)
        if self.request.view_name == 'edit':
            attendees = self.model.course_event.possible_bookers(
                external_only=False
            )
            return (self.attendee_choice(a) for a in attendees)

        else:
            raise NotImplementedError

    def on_request(self):
        if self.request.view_name == 'add-placeholder':
            self.delete_field('attendee_id')
        else:
            self.attendee_id.choices = self.get_attendee_choices()
            self.delete_field('dummy_desc')
        self.course_event_id.choices = self.get_event_choices()


class EditFsiReservationForm(AddFsiReservationForm):

    """
    The view of this form is not accessible for members
    """

    @property
    def attendee_collection(self):
        return CourseAttendeeCollection(self.request.session)

    def update_model(self, model):
        model.attendee_id = self.attendee_id.data
        model.course_event_id = self.course_event_id.data
        if model.is_placeholder:
            model.dummy_desc = self.dummy_desc.data

    def get_event_choices(self):
        return [self.event_choice(self.model.course_event)]
