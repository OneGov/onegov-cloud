from datetime import datetime

import pytz
from sedate import utcnow

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

    if form.submitted(request):
        data = form.get_useful_data()
        self.course_id = data['course_id']

        if request.current_attendee.role != 'editor':
            self.organisation = data['organisation']

        return {
            'layout': layout,
            'model': self,
            'results': self.query().all(),
            'form': form,
            'button_text': _('Create Audit'),
            'now': now,
        }

    return {
        'layout': layout,
        'model': self,
        'results': None,
        'form': form,
        'button_text': _('Create Audit'),
        'now': now,
    }
