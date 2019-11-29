from wtforms import StringField
from wtforms.validators import InputRequired, Email
from wtforms.fields.html5 import EmailField

from onegov.form.fields import ChosenSelectMultipleField
from onegov.fsi import _
from onegov.form import Form
from onegov.fsi.models import CourseAttendee


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
        model.permissions = self.permissions.data

    def apply_model(self, model):
        self.first_name.data = model.first_name
        self.last_name.data = model.last_name
        self.permissions.data = model.permissions

    def on_request(self):
        if self.request.view_name != 'add-external':
            self.delete_field('email')
            self.permissions.choices = [
                (p.code, p.code)
                for p in self.unique_permission_codes() if p.code
            ]
        else:
            self.delete_field('permissions')
