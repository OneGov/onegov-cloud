from __future__ import annotations

from functools import cached_property
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.fsi import _
from onegov.fsi.models import CourseAttendee
from wtforms.fields import SelectField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.collections.audit import AuditCollection
    from onegov.fsi.request import FsiRequest
    from uuid import UUID
    from wtforms.fields.choices import _Choice


class AuditForm(Form):

    model: AuditCollection
    request: FsiRequest

    course_id = SelectField(
        label=_('Course'),
        choices=[],
        validators=[
            InputRequired()
        ],
        description=_('Hidden courses or courses without '
                      'mandatory refresh are not in the list'),
    )

    organisations = ChosenSelectMultipleField(
        label=_('By Organisation'),
        choices=[],
    )

    letter = SelectField(
        label='Always Hidden, used for redirection persistence',
        choices=[]
    )

    @property
    def none_choice(self) -> tuple[str, str]:
        return '', self.request.translate(_('None'))

    @cached_property
    def distinct_organisations(self) -> tuple[str, ...]:
        query = self.request.session.query(CourseAttendee.organisation).filter(
            CourseAttendee.organisation.isnot(None)).distinct()
        query = query.order_by(CourseAttendee.organisation)
        return tuple(a.organisation for a in query)

    @cached_property
    def courses(self) -> tuple[tuple[UUID, str], ...]:
        return self.model.relevant_courses

    @cached_property
    def need_course_selection(self) -> bool:
        return len(self.courses) > 1 if self.courses else True

    @property
    def att(self) -> CourseAttendee:
        # NOTE: We assume that every user is a CourseAttendee
        return self.request.attendee  # type:ignore[return-value]

    def get_course_choices(self) -> list[_Choice]:
        if not self.courses:
            return [self.none_choice]
        return [(str(course_id), name) for course_id, name in self.courses]

    def for_admins(self) -> None:
        self.organisations.choices = [
            (e, e) for e in self.distinct_organisations] or [self.none_choice]
        self.organisations.validators = []
        if self.model.organisations and self.request.method == 'GET':
            self.organisations.data = self.model.organisations

    def for_editors(self) -> None:
        assert self.att is not None
        permissions = self.att.permissions or []
        self.organisations.choices = (
            sorted((p, p) for p in permissions) or [self.none_choice])

        if self.model.organisations and self.request.method == 'GET':
            self.organisations.data = self.model.organisations
        else:
            self.select_all('organisations')

    def select_all(self, name: str) -> None:
        field = self[name]
        if not field.data:
            assert hasattr(field, 'choices')
            field.data = [value for value, label in field.choices]

    def on_request(self) -> None:
        self.course_id.choices = self.get_course_choices()
        if not self.need_course_selection:
            self.hide(self.course_id)

        self.hide(self.letter)
        self.letter.choices = [(le, le) for le in self.model.used_letters]
        self.letter.choices.insert(0, self.none_choice)
        if self.model.letter:
            self.letter.data = self.model.letter
        else:
            self.letter.data = ''

        if self.att.role == 'admin':
            self.for_admins()
        else:
            self.for_editors()
