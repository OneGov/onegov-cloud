import sedate

from onegov.form.fields import TimezoneDateTimeField, ChosenSelectField

from wtforms import StringField, IntegerField, BooleanField
from wtforms.validators import InputRequired

from onegov.fsi import _
from onegov.form import Form
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.models.course_event import course_status_choices, CourseEvent


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

    locked_for_subscriptions = BooleanField(
        label=_("Locked for Subscriptions"),
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
        choices=[],
    )

    def ensure_start_before_end(self):
        if self.start.data >= self.end.data:
            self.start.errors = [_("Please use a start prior to the end")]
            return False

    def ensure_no_duplicates(self):
        if not isinstance(self.model, CourseEventCollection):
            return  # skip for edit views
        if self.start.data and self.end.data and self.course_id.data:
            existing = self.request.session.query(CourseEvent).filter_by(
                start=self.start.data,
                end=self.end.data,
                course_id=self.course_id.data
            ).first()
            if existing:
                self.course_id.errors.append(
                    _('A duplicate event already exists')
                )
                return False

    def on_request(self):
        collection = CourseCollection(self.request.session)
        if self.model.course_id:
            course = collection.by_id(self.model.course_id)
            self.course_id.choices = (str(course.id), course.name),
        else:
            self.course_id.choices = tuple(
                (str(c.id), c.name) for c in collection.query()
            )

        self.status.choices = course_status_choices(self.request)
        self.status.default = 'created'

    @staticmethod
    def fix_utc_to_local_time(db_time):
        # Todo: TimezoneDateTimeField.process_data is not called when applying
        # the date from the database in apply model
        return db_time and sedate.to_timezone(
            db_time, 'Europe/Zurich') or db_time

    def apply_model(self, model):
        self.location.data = model.location
        self.presenter_name.data = model.presenter_name
        self.presenter_company.data = model.presenter_company
        self.presenter_email.data = model.presenter_email
        self.hidden_from_public.data = model.hidden_from_public
        self.locked_for_subscriptions.data = model.locked_for_subscriptions

        self.start.data = self.fix_utc_to_local_time(model.start)
        self.end.data = self.fix_utc_to_local_time(model.end)
        self.min_attendees.data = model.min_attendees
        self.max_attendees.data = model.max_attendees
        self.status.data = model.status

    def update_model(self, model):
        model.location = self.location.data
        model.presenter_name = self.presenter_name.data
        model.presenter_company = self.presenter_company.data
        model.presenter_email = self.presenter_email.data
        model.hidden_from_public = self.hidden_from_public.data
        model.locked_for_subscriptions = self.locked_for_subscriptions.data

        model.start = self.start.data
        model.end = self.end.data
        model.min_attendees = self.min_attendees.data
        model.max_attendees = self.max_attendees.data
        model.status = self.status.data
        model.hidden_from_public = self.hidden_from_public.data
