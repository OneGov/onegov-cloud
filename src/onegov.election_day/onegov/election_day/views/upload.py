""" The upload view. """

from onegov.ballot import Vote
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import UploadForm
from onegov.election_day.layout import ManageLayout


@ElectionDayApp.form(model=Vote, name='upload', template='upload.pt',
                     permission=Private, form=UploadForm)
def view_upload(self, request, form):

    if form.submitted(request):
        pass

    return {
        'layout': ManageLayout(self, request),
        'title': self.title,
        'subtitle': _("Upload results"),
        'form': form
    }
