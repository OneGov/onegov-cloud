from __future__ import annotations

from sqlalchemy import desc
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.fsi import _
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from onegov.fsi.models import CourseEvent, CourseSubscription


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.models import (
        CourseAttendee)
    from onegov.fsi.request import FsiRequest
    from wtforms.fields.choices import _Choice


class SubscriptionFormMixin:

    model: CourseSubscription
    request: FsiRequest

    @property
    def event(self) -> CourseEvent:
        return self.model.course_event

    @property
    def event_collection(self) -> CourseEventCollection:
        return CourseEventCollection(
            self.request.session,
            upcoming_only=True,
            show_hidden=self.request.is_manager,
            show_locked=self.request.is_admin
        )

    @property
    def attendee(self) -> CourseAttendee | None:
        return self.model.attendee

    def event_choice(self, event: CourseEvent) -> tuple[str, str]:
        return str(event.id), str(event)

    def attendee_choice(
        self,
        attendee: CourseAttendee | None
    ) -> tuple[str, str]:
        if not attendee:
            return self.none_choice
        text = str(attendee)
        if attendee.organisation:
            text = f'{text}, {attendee.organisation}'
        if attendee.user_id and attendee.source_id:
            text += f' | {attendee.source_id}'
        return str(attendee.id), text

    @property
    def none_choice(self) -> tuple[str, str]:
        return '', self.request.translate(_('None'))


class AddFsiSubscriptionForm(Form, SubscriptionFormMixin):

    request: FsiRequest

    attendee_id = ChosenSelectField(
        label=_('Attendee'),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    course_event_id = ChosenSelectField(
        label=_('Course Event'),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    @property
    def attendee_collection(self) -> CourseAttendeeCollection:
        # Already filtered by the organisations if auth_attendee is an editor
        return CourseAttendeeCollection(
            self.request.session,
            external_only=self.model.external_only,
            auth_attendee=self.request.attendee
        )

    def get_event_choices(self) -> list[_Choice]:

        if self.model.course_event_id:
            return [self.event_choice(self.event)]

        if self.model.attendee_id:
            assert self.attendee is not None
            # Filters courses he registered
            events = self.attendee.possible_course_events(
                show_hidden=self.request.is_manager,
                show_locked=self.request.is_admin
            )
        else:
            events = self.event_collection.query()

        return [self.event_choice(e) for e in events] or [self.none_choice]

    def get_attendee_choices(self) -> list[_Choice]:

        if self.model.attendee_id:
            return [self.attendee_choice(self.attendee)]

        if self.model.course_event_id:
            attendees = self.event.possible_subscribers(
                external_only=self.model.external_only,
                auth_attendee=self.model.auth_attendee
            )
        else:
            attendees = self.attendee_collection.query()
        return [
            self.attendee_choice(a) for a in attendees] or [self.none_choice]

    def on_request(self) -> None:
        self.attendee_id.choices = self.get_attendee_choices()
        self.attendee_id.default = [self.attendee_choice(self.attendee)]
        self.course_event_id.choices = self.get_event_choices()

    @property
    def event_from_form(self) -> CourseEvent | None:
        return self.course_event_id.data and CourseEventCollection(
            self.request.session,
            show_hidden=True,
            show_locked=True
        ).by_id(self.course_event_id.data) or None

    def ensure_no_other_subscriptions(self) -> bool:
        if self.attendee_id.data and self.course_event_id.data:
            event = self.event_from_form
            if not event:
                assert isinstance(self.course_event_id.errors, list)
                self.course_event_id.errors.append(
                    _('The selected course was deleted. '
                      'Please refresh the page')
                )
                return False
            if not event.can_book(self.attendee_id.data):
                assert isinstance(self.attendee_id.errors, list)
                self.attendee_id.errors.append(
                    _('There are other subscriptions for '
                      'the same course in this year')
                )
                return False
        return True

    def ensure_6_year_time_interval(self) -> bool:
        if self.attendee_id.data and self.event_from_form:
            if self.request.is_admin:
                return True
            if not self.event_from_form.exceeds_six_year_limit(
                self.attendee_id.data,
                self.request
            ):
                last_subscribed_event = self.request.session.query(
                    CourseEvent).join(CourseSubscription).filter(
                    CourseSubscription.attendee_id == self.attendee_id.data
                    ).order_by(desc(CourseEvent.start)).first()
                assert last_subscribed_event is not None
                assert isinstance(self.course_event_id.errors, list)
                self.course_event_id.errors.append(
                    _('The selected course must take place at least 6 years '
                      'after the last course for which the attendee was '
                      'registered. The last course for this attendee was '
                      'on ${date}.', mapping={
                          'date': last_subscribed_event.start.strftime(
                                '%d.%m.%Y')}
                          )
                )
                return False
        return True

    def ensure_can_book_if_locked(self) -> bool:
        if self.attendee_id.data and self.course_event_id.data:
            event = self.event_from_form
            if not event:
                assert isinstance(self.course_event_id.errors, list)
                self.course_event_id.errors.append(
                    _('The selected course was deleted. '
                      'Please refresh the page')
                )
                return False
            if event.locked and not self.request.is_admin:
                assert isinstance(self.course_event_id.errors, list)
                self.course_event_id.errors.append(
                    _("This course event can't be booked (anymore).")
                )
                return False
        return True


class AddFsiPlaceholderSubscriptionForm(Form, SubscriptionFormMixin):

    request: FsiRequest

    course_event_id = ChosenSelectField(
        label=_('Course Event'),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    dummy_desc = StringField(
        label=_('Placeholder Description (optional)'),
    )

    def get_event_choices(self) -> list[_Choice]:

        if self.model.course_event_id:
            return [self.event_choice(self.event)]

        events = self.event_collection.query()
        if self.model.attendee_id:
            assert self.attendee is not None

            # Filters courses he registered
            events = self.attendee.possible_course_events(
                show_hidden=self.request.is_manager,
                show_locked=self.request.is_admin
            )
        return [self.event_choice(e) for e in events] or [self.none_choice]

    def on_request(self) -> None:
        self.course_event_id.choices = self.get_event_choices()


class EditFsiSubscriptionForm(Form, SubscriptionFormMixin):
    """
    The view of this form is not accessible for members
    """

    request: FsiRequest

    attendee_id = ChosenSelectField(
        label=_('Attendee'),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    course_event_id = ChosenSelectField(
        label=_('Course Event'),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    @property
    def attendee_collection(self) -> CourseAttendeeCollection:
        """Since this view will only be used by admin, just get
        the whole list of attendees"""
        return CourseAttendeeCollection(self.request.session)

    def update_model(self, model: CourseSubscription) -> None:
        model.attendee_id = self.attendee_id.data
        model.course_event_id = self.course_event_id.data

    def apply_model(self, model: CourseSubscription) -> None:
        self.course_event_id.data = model.course_event_id
        self.attendee_id.data = model.attendee_id

    def get_event_choices(self) -> list[_Choice]:
        return [self.event_choice(self.model.course_event)]

    def get_attendee_choices(self) -> list[_Choice]:
        attendees = self.model.course_event.possible_subscribers(
            external_only=False
        )
        choices: list[_Choice] = [self.attendee_choice(a) for a in attendees]
        choices.insert(0, self.attendee_choice(self.attendee))
        return choices

    def on_request(self) -> None:
        self.course_event_id.choices = self.get_event_choices()
        self.attendee_id.choices = self.get_attendee_choices()


class EditFsiPlaceholderSubscriptionForm(Form, SubscriptionFormMixin):

    request: FsiRequest

    course_event_id = ChosenSelectField(
        label=_('Course Event'),
        choices=[],
        validators=[InputRequired()]
    )

    dummy_desc = StringField(
        label=_('Placeholder Description (optional)'),
    )

    def update_model(self, model: CourseSubscription) -> None:
        desc = self.dummy_desc.data
        if not desc:
            default_desc = self.request.translate(
                _('Placeholder Subscription'))
            desc = default_desc
        model.course_event_id = self.course_event_id.data
        model.dummy_desc = desc

    def apply_model(self, model: CourseSubscription) -> None:
        self.course_event_id.data = model.course_event_id
        self.dummy_desc.data = model.dummy_desc

    def get_event_choices(self) -> list[_Choice]:
        return [self.event_choice(self.model.course_event)]

    def on_request(self) -> None:
        self.course_event_id.choices = self.get_event_choices()
