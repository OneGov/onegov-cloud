from sedate import utcnow

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.fsi import FsiApp
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.forms.audit import AuditForm
from onegov.fsi.layouts.audit import AuditLayout
from onegov.fsi import _


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
