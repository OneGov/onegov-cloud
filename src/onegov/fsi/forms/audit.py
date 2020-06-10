from cached_property import cached_property
from wtforms import SelectField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.fsi import _
from onegov.fsi.models import CourseAttendee


class AuditForm(Form):

    course_id = SelectField(
        label=_("Course"),
        choices=[],
        validators=[
            InputRequired()
        ],
        description=_('Hidden courses or courses without '
                      'mandatory refresh are not in the list'),
    )

    organisations = ChosenSelectMultipleField(
        label=_("By Organisation"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    @property
    def none_choice(self):
        return '', self.request.translate(_('None'))

    @cached_property
    def distinct_organisations(self):
        query = self.request.session.query(CourseAttendee.organisation).filter(
            CourseAttendee.organisation != None).distinct()
        query = query.order_by(CourseAttendee.organisation)
        return tuple(a.organisation for a in query)

    @cached_property
    def courses(self):
        return self.model.relevant_courses

    @cached_property
    def need_course_selection(self):
        return len(self.courses) > 1 if self.courses else True

    @property
    def att(self):
        return self.request.current_attendee

    def get_course_choices(self):
        if not self.courses:
            return self.none_choice
        return tuple((str(c.id), c.name) for c in self.courses)

    def for_admins(self):
        self.organisations.choices = tuple(
            (e, e) for e in self.distinct_organisations) or [self.none_choice]
        self.organisations.validators = []
        if self.model.organisations:
            self.organisations.data = self.model.organisations

    def for_editors(self):

        permissions = self.att.permissions or []
        choices = sorted((p, p) for p in permissions) or [self.none_choice]
        self.organisations.choices = choices

        if self.model.organisations:

            self.organisations.data = self.model.organisations
        else:
            self.select_all('organisations')

    def select_all(self, name):
        field = getattr(self, name)
        if not field.data:
            field.data = list(next(zip(*field.choices)))

    def on_request(self):
        # Roves crf token from query params since it's a get form
        if hasattr(self, 'csrf_token'):
            self.delete_field('csrf_token')

        self.course_id.choices = self.get_course_choices()
        if not self.need_course_selection:
            self.hide(self.course_id)

        if self.att.role == 'admin':
            self.for_admins()
        else:
            self.for_editors()
