from wtforms import StringField, SelectField, TextAreaField
from wtforms.validators import InputRequired, Email

from onegov.form.parser.core import EmailField
from onegov.fsi import _
from onegov.form import Form
from onegov.fsi.models.course_attendee import attendee_title_choices


class CourseAttendeeForm(Form):

    title = SelectField(
        label=_('Salutation'),
        choices=attendee_title_choices(),
        render_kw={'size': 2}
    )

    first_name = StringField(
        label=_('First Name'),
        render_kw={'size': 5},
        validators=[InputRequired()]
    )

    last_name = StringField(
        label=_('First Name'),
        render_kw={'size': 5},
        validators=[InputRequired()]
    )

    address = TextAreaField(
        label=_('Address'),
        render_kw={'cols': 12, 'rows': 4}
    )

    def update_model(self, model):
        model.title = self.title.data
        model.first_name = self.first_name.data
        model.last_name = self.last_name.data
        model.address = self.address.data

    def apply_model(self, model):
        self.title.data = model.title
        self.first_name.data = model.first_name
        self.last_name.data = model.last_name
        self.address.data = model.address


class ExternalCourseAttendeeForm(CourseAttendeeForm):

    email = EmailField(
        label=_('Email'),
        validators=[InputRequired(), Email()],
        required=True
    )
