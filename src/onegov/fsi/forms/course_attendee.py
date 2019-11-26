from wtforms import StringField
from wtforms.validators import InputRequired, Email
from wtforms.fields.html5 import EmailField
from onegov.fsi import _
from onegov.form import Form


class CourseAttendeeForm(Form):

    first_name = StringField(
        label=_('First Name'),
        render_kw={'size': 3},
        validators=[InputRequired()]
    )

    last_name = StringField(
        label=_('Last Name'),
        render_kw={'size': 4},
        validators=[InputRequired()],
    )

    email = EmailField(
        label=_('Email'),
        validators=[InputRequired(), Email()],
        render_kw={'size': 4},
    )

    def update_model(self, model):
        model.first_name = self.first_name.data
        model.last_name = self.last_name.data

    def apply_model(self, model):
        self.first_name.data = model.first_name
        self.last_name.data = model.last_name

    def on_request(self):
        if self.request.view_name != 'add-external':
            self.delete_field('email')
