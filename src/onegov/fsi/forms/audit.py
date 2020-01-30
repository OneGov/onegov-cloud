from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.fsi import _
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.models import CourseAttendee, Course


class AuditForm(Form):

    course_id = ChosenSelectField(
        label=_("Course"),
        choices=[],
        validators=[
            InputRequired()
        ],
        description=_('Hidden courses or courses without '
                      'mandatory refresh are not in the list')
    )

    organisation = ChosenSelectField(
        label=_("Organisation"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    @property
    def none_choice(self):
        return '', self.request.translate(_('None'))

    @property
    def course_collection(self):
        return CourseCollection(
            self.request.session, self.request.current_attendee)

    def get_organisation_choices(self):
        att = self.request.current_attendee
        if att.role == 'editor':
            return [(p, p) for p in att.permissions] or self.none_choice

        session = self.request.session
        results = session.query(CourseAttendee.organisation).filter(
            CourseAttendee.organisation != None).distinct()
        return [(e.organisation, e.organisation) for e in results]\
            or self.none_choice

    def get_course_choices(self):
        session = self.request.session
        results = session.query(Course).filter_by(hidden_from_public=False)
        results = results.filter(Course.mandatory_refresh != None)
        return [(str(c.id), c.name) for c in results] or self.none_choice

    def on_request(self):
        self.course_id.choices = self.get_course_choices()
        self.organisation.choices = self.get_organisation_choices()

