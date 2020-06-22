from sedate import utcnow
from webob import Response

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.utils import normalize_for_url
from onegov.fsi import FsiApp
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.forms.audit import AuditForm
from onegov.fsi.layouts.audit import AuditLayout
from onegov.fsi import _
from onegov.fsi.pdf import FsiPdf


def set_cached_choices(request, organisations):
    browser_session = request.browser_session
    browser_session['last_chosen_organisations'] = organisations or ''


def cached_org_choices(request):
    return request.browser_session.get('last_chosen_organisations')


@FsiApp.form(
    model=AuditCollection,
    template='audits.pt',
    permission=Private,
    form=AuditForm
)
def invite_attendees_for_event(self, request, form):
    layout = AuditLayout(self, request)
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
                self.by_letter_and_orgs(
                    letter=letter if (letter != self.letter) else None
                )
            ),
            active=(letter == self.letter),
        ) for letter in self.used_letters
    )

    return {
        'layout': layout,
        'model': self,
        'results': self.batch if self.course_id else [],
        'form': form,
        'button_text': _('Update'),
        'now': now,
        'letters': letters
    }


@FsiApp.view(
    model=AuditCollection,
    name='pdf',
    permission=Private
)
def get_audit_pdf(self, request):
    if not self.course_id:
        return Response(status='503 Service Unavailable')

    title = request.translate(
        _("Audit for ${course_name}",
          mapping={'course_name': self.course.name})

    )
    result = FsiPdf.from_audit_collection(
        self, AuditLayout(self, request), title)

    return Response(
        result.read(),
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url("audit-fsi")
        )
    )
