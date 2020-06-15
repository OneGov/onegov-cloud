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


@FsiApp.form(
    model=AuditCollection,
    template='audits.pt',
    permission=Private,
    form=AuditForm
)
def invite_attendees_for_event(self, request, form):
    layout = AuditLayout(self, request)
    now = utcnow()
    form.method = 'GET'

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

    return {
        'layout': layout,
        'model': self,
        'results': self.batch,
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
    title = request.translate(
        _("Audit for ${course_name}",
          mapping={'course_name': self.course.name})

    )
    result = FsiPdf.from_audit_collection(
        request, self, AuditLayout(self, request), title)
    # with open(result, 'rb') as file:
    #     result = file.read()

    return Response(
        result.read(),
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url("audit-fsi")
        )
    )
