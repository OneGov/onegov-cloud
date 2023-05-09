from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.fsi import _
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class SubscriptionFormMixin:

    @property
    def event(self):
        return self.model.course_event

    @property
    def event_collection(self):
        return CourseEventCollection(
            self.request.session,
            upcoming_only=True,
            show_hidden=self.request.is_manager,
            show_locked=self.request.is_admin
        )

    @property
    def attendee(self):
        return self.model.attendee

    def event_choice(self, event):
        return str(event.id), str(event)

    def attendee_choice(self, attendee):
        if not attendee:
            return self.none_choice
        text = str(attendee)
        if attendee.organisation:
            text = f'{text}, {attendee.organisation}'
        if attendee.user_id and attendee.source_id:
            text += f' | {attendee.source_id}'
        return str(attendee.id), text

    @property
    def none_choice(self):
        return '', self.request.translate(_('None'))


class AddFsiSubscriptionForm(Form, SubscriptionFormMixin):

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
        # Already filtered by the organisations if auth_attendee is an editor
        return CourseAttendeeCollection(
            self.request.session,
            external_only=self.model.external_only,
            auth_attendee=self.request.attendee
        )

    def get_event_choices(self):

        if self.model.course_event_id:
            return self.event_choice(self.event),

        if self.model.attendee_id:

            # Filters courses he registered
            events = self.attendee.possible_course_events(
                show_hidden=self.request.is_manager,
                show_locked=self.request.is_admin
            )
        else:
            events = self.event_collection.query()

        if not events.first():
            return [self.none_choice]
        return tuple(self.event_choice(e) for e in events)

    def get_attendee_choices(self):

        if self.model.attendee_id:
            return self.attendee_choice(self.attendee),

        if self.model.course_event_id:
            attendees = self.event.possible_subscribers(
                external_only=self.model.external_only,
                auth_attendee=self.model.auth_attendee
            )
        else:
            attendees = self.attendee_collection.query()
        return tuple(
            self.attendee_choice(a) for a in attendees) or [self.none_choice]

    def on_request(self):
        self.attendee_id.choices = self.get_attendee_choices()
        self.attendee_id.default = [self.attendee_choice(self.attendee)]
        self.course_event_id.choices = self.get_event_choices()

    @property
    def event_from_form(self):
        return self.course_event_id.data and CourseEventCollection(
            self.request.session,
            show_hidden=True,
            show_locked=True
        ).by_id(self.course_event_id.data)

    def ensure_no_other_subscriptions(self):
        if self.attendee_id.data and self.course_event_id.data:
            event = self.event_from_form
            if not event:
                self.course_event_id.errors.append(
                    _("The selected course was deleted. "
                      "Please refresh the page")
                )
                return False
            if not event.can_book(self.attendee_id.data):
                self.attendee_id.errors.append(
                    _("There are other subscriptions for "
                      "the same course in this year")
                )
                return False

    def ensure_can_book_if_locked(self):
        if self.attendee_id.data and self.course_event_id.data:
            event = self.event_from_form
            if not event:
                self.course_event_id.errors.append(
                    _("The selected course was deleted. "
                      "Please refresh the page")
                )
                return False
            if event.locked and not self.request.is_admin:
                self.course_event_id.errors.append(
                    _("This course event can't be booked (anymore).")
                )
                return False


class AddFsiPlaceholderSubscriptionForm(Form, SubscriptionFormMixin):

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

    def get_event_choices(self):

        if self.model.course_event_id:
            return self.event_choice(self.event),

        events = self.event_collection.query()
        if self.model.attendee_id:

            # Filters courses he registered
            events = self.attendee.possible_course_events(
                show_hidden=self.request.is_manager,
                show_locked=self.request.is_admin
            )
        return tuple(
            self.event_choice(e) for e in events) or [self.none_choice]

    def on_request(self):
        self.course_event_id.choices = self.get_event_choices()


class EditFsiSubscriptionForm(Form, SubscriptionFormMixin):

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
        attendees = self.model.course_event.possible_subscribers(
            external_only=False
        )
        choices = [self.attendee_choice(self.attendee)]
        return choices + [self.attendee_choice(a) for a in attendees]

    def on_request(self):
        self.course_event_id.choices = self.get_event_choices()
        self.attendee_id.choices = self.get_attendee_choices()


class EditFsiPlaceholderSubscriptionForm(Form, SubscriptionFormMixin):

    course_event_id = ChosenSelectField(
        label=_("Course Event"),
        choices=[],
        validators=[InputRequired()]
    )

    dummy_desc = StringField(
        label=_('Placeholder Description (optional)'),
    )

    def update_model(self, model):
        desc = self.dummy_desc.data
        if not desc:
            default_desc = self.request.translate(
                _('Placeholder Subscription'))
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
