
from onegov.form.fields import TimezoneDateTimeField, ChosenSelectField

from wtforms import StringField, IntegerField, BooleanField
from wtforms.validators import InputRequired

from onegov.fsi import _
from onegov.form import Form
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.models.course_event import course_status_choices


class CourseEventForm(Form):

    course_id = ChosenSelectField(
        label=_('Course'),
        choices=[],
    )

    presenter_name = StringField(
        label=_('Presenter'),
        description=_('Full name of the presenter'),
        validators=[
            InputRequired()
        ]
    )

    presenter_company = StringField(
        label=_('Company'),
        description='Presenters company',
        validators=[
            InputRequired()
        ]
    )

    presenter_email = StringField(
        label=_('Presenter Email'),
        validators=[
            InputRequired()
        ]
    )

    hidden_from_public = BooleanField(
        label=_("Hidden"),
        default=False,
    )

    # Course Event info
    start = TimezoneDateTimeField(
        label=_('Course Start'),
        timezone='Europe/Zurich',
        validators=[
            InputRequired()
        ]
    )

    end = TimezoneDateTimeField(
        label=_('Course End'),
        timezone='Europe/Zurich',
        validators=[
            InputRequired()
        ]
    )

    location = StringField(
        label=_('Location'),
        validators=[
            InputRequired()
        ],
        description=_('Address and Room')
    )

    min_attendees = IntegerField(
        label=_('Attendees min'),
        default=1
    )

    max_attendees = IntegerField(
        label=_('Attendees max'),
        validators=[
            InputRequired()
        ],
    )

    status = ChosenSelectField(
        label=_('Status'),
        choices=course_status_choices(),
        default='created'
    )

    def on_request(self):
        collection = CourseCollection(self.request.session)
        if self.model.course_id:
            course = collection.by_id(self.model.course_id)
            self.course_id.choices = (str(course.id), course.name),
        else:
            self.course_id.choices = tuple(
                (str(c.id), c.name) for c in collection.query()
            )

    def apply_model(self, model):
        self.location.data = model.location
        self.presenter_name.data = model.presenter_name
        self.presenter_company.data = model.presenter_company
        self.presenter_email.data = model.presenter_email
        self.hidden_from_public.data = model.hidden_from_public

        self.start.data = model.start
        self.end.data = model.end
        self.min_attendees.data = model.min_attendees
        self.max_attendees.data = model.max_attendees
        self.status.data = model.status

    def update_model(self, model):
        model.location = self.location.data
        model.presenter_name = self.presenter_name.data
        model.presenter_company = self.presenter_company.data
        model.presenter_email = self.presenter_email.data
        model.hidden_from_public = self.hidden_from_public.data

        model.start = self.start.data
        model.end = self.end.data
        model.min_attendees = self.min_attendees.data
        model.max_attendees = self.max_attendees.data
        model.status = self.status.data
        model.hidden_from_public = self.hidden_from_public.data
