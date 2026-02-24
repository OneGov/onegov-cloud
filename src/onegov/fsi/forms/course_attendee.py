from __future__ import annotations

from functools import cached_property
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField, ChosenSelectField
from onegov.fsi import _
from onegov.fsi.models import CourseAttendee
from onegov.fsi.models.course_attendee import external_attendee_org
from onegov.user import User
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.validators import InputRequired, Email


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.request import FsiRequest


class CourseAttendeeForm(Form):

    request: FsiRequest

    first_name = StringField(
        label=_('First Name'),
        validators=[InputRequired()]
    )

    last_name = StringField(
        label=_('Last Name'),
        validators=[InputRequired()],
    )

    email = EmailField(
        label=_('Email'),
        validators=[InputRequired(), Email()],
    )

    organisation = ChosenSelectField(
        label=_('Organisation'),
        choices=[],
    )

    permissions = ChosenSelectMultipleField(
        label=_('Permissions'),
        choices=[]
    )

    @cached_property
    def unique_permission_codes(self) -> tuple[str, ...]:
        return tuple(
            code for code, in self.request.session.query(
                CourseAttendee.organisation.distinct().label('code')
            ).order_by(CourseAttendee.organisation).filter(
                CourseAttendee.organisation.isnot(None)
            )
        )

    def update_model(self, model: CourseAttendee) -> None:
        model.first_name = self.first_name.data
        model.last_name = self.last_name.data
        if self.permissions:
            model.permissions = self.permissions.data
        if self.email:
            model._email = self.email.data
        if self.organisation:
            model.organisation = self.organisation.data

    def apply_model(self, model: CourseAttendee) -> None:
        self.first_name.data = model.first_name
        self.last_name.data = model.last_name
        if self.permissions:
            self.permissions.data = model.permissions
        if self.email:
            self.email.data = model.email
        if self.organisation:
            self.organisation.data = model.organisation

    def set_organisation_choices(self) -> None:
        if self.request.is_admin:
            organisations = self.unique_permission_codes
        else:
            assert self.request.attendee is not None
            organisations = tuple(self.request.attendee.permissions or ())

        if external_attendee_org not in organisations:
            organisations = (external_attendee_org, *organisations)

        self.organisation.choices = [(org, org) for org in organisations]

    def on_request(self) -> None:
        # is an external
        if not self.model.user_id or self.model.user.role != 'editor':
            self.delete_field('permissions')
        else:
            self.delete_field('email')
            self.permissions.choices = [
                (code, code) for code in self.unique_permission_codes
            ]
        if self.model.user_id or not self.request.is_manager:
            self.delete_field('organisation')
        else:
            self.set_organisation_choices()


class AddExternalAttendeeForm(CourseAttendeeForm):

    def ensure_email_not_existing(self) -> bool:
        email = self.email.data
        session = self.request.session
        # NOTE: Even though we potentially perform a redundant EXISTS query
        #       it's still almost certainly faster, since we only have to
        #       submit a single query to the database, plus the database is
        #       probably smart enough to optimize the second query away if
        #       the first one returned TRUE and if it doesn't do that it's
        #       probably because it's faster this way (parallelism).
        att = session.query(CourseAttendee).filter_by(_email=email)
        user = session.query(User).filter_by(username=email)
        if session.query(att.exists() | user.exists()).scalar():
            assert isinstance(self.email.errors, list)
            self.email.errors.append(
                _('An attendee with this email already exists'))
            return False
        return True

    def on_request(self) -> None:
        self.delete_field('permissions')
        self.set_organisation_choices()
