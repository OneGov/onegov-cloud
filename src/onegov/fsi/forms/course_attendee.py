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


class ExternalCourseAttendeeForm(CourseAttendeeForm):

    email = EmailField(
        label=_('Email'),
        validators=[InputRequired(), Email()],
        required=True
    )


