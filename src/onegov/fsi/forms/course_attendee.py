from wtforms import StringField
from wtforms.validators import InputRequired, Email
from wtforms.fields.html5 import EmailField

from onegov.form.fields import ChosenSelectMultipleField, ChosenSelectField
from onegov.fsi import _
from onegov.form import Form
from onegov.fsi.models import CourseAttendee
from onegov.fsi.models.course_attendee import external_attendee_org
from onegov.user import User


class CourseAttendeeForm(Form):

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

    def unique_permission_codes(self):
        query = self.request.session.query(
            CourseAttendee.organisation.distinct().label('code'))
        return query.order_by(CourseAttendee.organisation)

    def update_model(self, model):
        model.first_name = self.first_name.data
        model.last_name = self.last_name.data
        if self.permissions:
            model.permissions = self.permissions.data
        if self.email:
            model._email = self.email.data
        if self.organisation:
            model.organisation = self.organisation.data

    def apply_model(self, model):
        self.first_name.data = model.first_name
        self.last_name.data = model.last_name
        if self.permissions:
            self.permissions.data = model.permissions
        if self.email:
            self.email.data = model.email
        if self.organisation:
            self.organisation.data = model.organisation

    def set_organisation_choices(self):

        if self.request.is_admin:
            organisations = tuple(
                p.code for p in self.unique_permission_codes() if p.code)
            if external_attendee_org not in organisations:
                organisations = (external_attendee_org,) + organisations
        else:
            organisations = tuple(self.request.attendee.permissions)
            if not organisations:
                self.delete_field('organisation')
                return

        self.organisation.choices = [(org, org) for org in organisations]

    def on_request(self):
        # is an external
        if not self.model.user_id or self.model.user.role != 'editor':
            self.delete_field('permissions')
        else:
            self.delete_field('email')
            self.permissions.choices = [
                (p.code, p.code)
                for p in self.unique_permission_codes() if p.code
            ]


class AddExternalAttendeeForm(CourseAttendeeForm):

    def ensure_email_not_existing(self):
        email = self.email.data
        att = self.request.session.query(CourseAttendee).filter_by(
            _email=email).first()
        if att:
            self.email.errors.append(
                _("An attendee with this email already exists"))
            return False
        user = self.request.session.query(User).filter_by(
            username=email).first()
        if user:
            self.email.errors.append(
                _("An attendee with this email already exists"))
            return False

    def on_request(self):
        self.delete_field('permissions')
        self.set_organisation_choices()
