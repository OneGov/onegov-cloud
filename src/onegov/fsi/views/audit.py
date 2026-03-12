from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.fsi import _
from onegov.fsi import FsiApp
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.forms.audit import AuditForm
from onegov.fsi.layouts.audit import AuditLayout
from onegov.fsi.pdf import FsiPdf
from onegov.fsi.models import CourseAttendee
from sedate import utcnow
from webob import Response


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fsi.request import FsiRequest


def set_cached_choices(
    request: FsiRequest,
    organisations: list[str] | None
) -> None:
    browser_session = request.browser_session
    browser_session['last_chosen_organisations'] = organisations or None


def cached_org_choices(request: FsiRequest) -> list[str] | None:
    return request.browser_session.get('last_chosen_organisations')


@FsiApp.form(
    model=AuditCollection,
    template='audits.pt',
    permission=Private,
    form=AuditForm
)
def invite_attendees_for_event(
    self: AuditCollection,
    request: FsiRequest,
    form: AuditForm
) -> RenderData | Response:

    now = utcnow()

    if form.submitted(request):
        set_cached_choices(request, form.organisations.data)
        return request.redirect(request.link(
            self.__class__(
                session=self.session,
                auth_attendee=self.auth_attendee,
                organisations=form.organisations.data or None,
                letter=form.letter.data or None,
                page=0,
                course_id=self.course_id
            )
        ))

    cache = cached_org_choices(request)
    if cache and not self.organisations:
        return request.redirect(request.link(
            self.by_letter_and_orgs(
                orgs=[
                    o for o in cache if o in form.distinct_organisations
                ] or None
            )
        ))

    letters = tuple(
        Link(
            text=letter,
            url=request.link(
                self.by_letter(
                    letter=letter if (letter != self.letter) else None
                )
            ),
            active=(letter == self.letter),
        ) for letter in self.used_letters
    )

    next_subscriptions = self.next_subscriptions(request)
    recipient_ids = [
        r.id for r in self.cached_subset
        if not (next_subscriptions.get(r.id) or (
            r.start and r.refresh_interval and r.start.replace
            (year=r.start.year + r.refresh_interval) >= now))
    ] if self.course_id else []

    all_attendees = self.session.query(CourseAttendee).filter(
        CourseAttendee.id.in_(recipient_ids)
    ).all() if recipient_ids else []

    email_recipients = ('; '.join(a.email for a in all_attendees)
                        if len(all_attendees) < 100 else False)

    subject = request.translate(_('Reminder due course registration'))

    layout = AuditLayout(self, request)
    return {
        'layout': layout,
        'model': self,
        'results': self.batch if self.course_id else [],
        'form': form,
        'button_text': _('Update'),
        'now': now,
        'letters': letters,
        'email_recipients': email_recipients,
        'subject': subject,
        'next_subscriptions': next_subscriptions
    }


@FsiApp.view(
    model=AuditCollection,
    name='pdf',
    permission=Private
)
def get_audit_pdf(self: AuditCollection, request: FsiRequest) -> Response:
    if not self.course_id:
        # FIXME: Really, a 503 for this?
        return Response(status='503 Service Unavailable')

    assert self.course is not None
    title = request.translate(
        _('Audit for ${course_name}',
          mapping={'course_name': self.course.name})

    )
    result = FsiPdf.from_audit_collection(
        self, AuditLayout(self, request), title)

    return Response(
        result.read(),
        content_type='application/pdf',
        content_disposition='inline; filename=audit-fsi.pdf'
    )
