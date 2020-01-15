from wtforms import StringField
from wtforms.validators import InputRequired
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi import _


class ReservationFormMixin:

    @property
    def event(self):
        return self.model.course_event

    @property
    def attendee(self):
        return self.model.attendee

    def event_choice(self, event):
        return str(event.id), str(event)

    def attendee_choice(self, attendee):
        if not attendee:
            return '', self.request.translate(_('None'))
        text = f'{str(attendee)}'
        if attendee.user and attendee.user.source_id:
            text += f' | {attendee.user.source_id}'
        return str(attendee.id), text

    @property
    def none_choice(self):
        return '', self.request.translate(_('None'))


class AddFsiReservationForm(Form, ReservationFormMixin):

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
            external_only=self.model.external_only,
            auth_attendee=self.request.current_attendee
        )

    def get_event_choices(self):

        if self.model.course_event_id:
            return self.event_choice(self.event),

        if self.model.attendee_id:

            # Filters courses he registered
            events = self.attendee.possible_course_events(
                show_hidden=self.request.is_manager)
        else:
            events = self.event_collection.query()

        if not events.first():
            return [self.none_choice]
        return (self.event_choice(e) for e in events)

    def get_attendee_choices(self):
        assert self.request.view_name == 'add'

        if self.model.attendee_id:
            return self.attendee_choice(self.attendee),

        if self.model.course_event_id:
            attendees = self.event.possible_bookers(
                external_only=self.model.external_only
            )
        else:
            attendees = self.attendee_collection.query()
        return (
            self.attendee_choice(a) for a in attendees
        ) if attendees.first() else [self.none_choice]

    def on_request(self):
        self.attendee_id.choices = self.get_attendee_choices()
        self.attendee_id.default = [self.attendee_choice(self.attendee)]
        self.course_event_id.choices = self.get_event_choices()


class AddFsiPlaceholderReservationForm(Form, ReservationFormMixin):

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
    def event_collection(self):
        return CourseEventCollection(
            self.request.session,
            upcoming_only=True,
            show_hidden=self.request.is_manager
        )

    def get_event_choices(self):

        if self.model.course_event_id:
            return self.event_choice(self.event),

        events = self.event_collection.query()
        if self.model.attendee_id:

            # Filters courses he registered
            events = self.attendee.possible_course_events(
                show_hidden=self.request.is_manager
            )
        if not events.first():
            return [self.none_choice]
        return (self.event_choice(e) for e in events)

    def on_request(self):
        self.course_event_id.choices = self.get_event_choices()


class EditFsiReservationForm(Form, ReservationFormMixin):

    """
    The view of this form is not accessible for members
    """

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

    @property
    def attendee_collection(self):
        """Since this view will only be used by admin, just get
        the whole list of attendees"""
        return CourseAttendeeCollection(self.request.session)

    def update_model(self, model):
        model.attendee_id = self.attendee_id.data
        model.course_event_id = self.course_event_id.data

    def apply_model(self, model):
        self.course_event_id.data = model.course_event_id
        self.attendee_id.data = model.attendee_id

    def get_event_choices(self):
        return [self.event_choice(self.model.course_event)]

    def get_attendee_choices(self):
        attendees = self.model.course_event.possible_bookers(
            self.request.current_attendee,
            external_only=False
        )
        choices = [self.attendee_choice(self.attendee)]
        return choices + [self.attendee_choice(a) for a in attendees]

    def on_request(self):
        self.course_event_id.choices = self.get_event_choices()
        self.attendee_id.choices = self.get_attendee_choices()


class EditFsiPlaceholderReservationForm(Form, ReservationFormMixin):

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

    def update_model(self, model):
        desc = self.dummy_desc.data
        if not desc:
            default_desc = self.request.translate(_('Placeholder Reservation'))
            desc = default_desc
        model.course_event_id = self.course_event_id.data
        model.dummy_desc = desc

    def apply_model(self, model):
        self.course_event_id.data = model.course_event_id
        self.dummy_desc.data = model.dummy_desc

    def get_event_choices(self):
        return [self.event_choice(self.model.course_event)]

    def on_request(self):
        self.course_event_id.choices = self.get_event_choices()
