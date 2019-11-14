from wtforms import StringField
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

    dummy_desc = StringField(
        label=_('Placeholder Description (optional)'),
    )

    @property
    def event(self):
        return self.model.course_event

    @property
    def attendee(self):
        return self.model.attendee

    @property
    def event_collection(self):
        return CourseEventCollection(
            self.request.session,
            upcoming_only=True,
            show_hidden=self.request.is_manager
        )

    @property
    def attendee_collection(self):
        return CourseAttendeeCollection(self.request.session,
                                        external_only=self.model.external_only)

    @property
    def none_choice(self):
        return '', _('None')

    def get_event_choices(self):
        choices = self.event_collection.query()
        # Filter courses he registered
        if self.attendee:
            if isinstance(self, CourseEventCollection):
                event_model = self.model.model_class
            else:
                event_model = self.model.__class__
            choices = self.event_choices.filter(
                event_model.attendee_id != self.attendee.id)
        return (self.event_choice(e) for e in choices)

    @staticmethod
    def attendee_choice(attendee):
        return str(attendee.id), f'{str(attendee)} - {attendee.email}'

    def get_attendee_choices(self):
        result = [self.none_choice]
        query = self.attendee_collection.query()
        return tuple(result + [self.attendee_choice(a) for a in query])

    @property
    def dealing_with_placeholder(self):
        return (self.request.view_name == 'add-placeholder'
                or not self.attendee)

    @property
    def edits_placeholder(self):
        return self.request.view_name == 'edit' and not self.attendee

    @staticmethod
    def event_choice(event):
        return str(event.id), event.name

    @property
    def from_scratch(self):
        return not self.attendee and not self.event

    def populate_choices(self):
        if self.edits_placeholder or self.from_scratch:
            self.attendee_id.choices = self.get_attendee_choices()
            self.attendee_id.default = self.none_choice[0]
        elif self.dealing_with_placeholder and not self.from_scratch:
            self.delete_field('attendee_id')
        else:
            self.attendee_id.choices = (self.attendee_choice(self.attendee),)
            self.delete_field('dummy_desc')

        if self.event:
            self.course_event_id.choices = (self.event_choice(self.event),)
        else:
            self.course_event_id.choices = self.get_event_choices()

    def on_request(self):
        """
        - self.model is the reservation_collection of the view using the form
        . the collection has the property course_event or attendee
        - in path.py, the attendee_id is set using the request if not a manager
        - self.model.attendee will be filled always if the user is not manager
        - if attendee is None, this is a placeholder reservation

        """
        self.populate_choices()


class EditFsiReservationForm(FsiReservationForm):

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


