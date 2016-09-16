import morepath

from onegov.core.security import Public
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.models import VacationActivity
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.forms import VacationActivityForm
from onegov.feriennet.layout import (
    NewVacationActivityLayout,
    VacationActivityCollectionLayout
)


@FeriennetApp.html(model=VacationActivityCollection, template='activities.pt',
                   permission=Public)
def view_vacation_activities(self, request):

    return {
        'activities': self.query().all(),
        'layout': VacationActivityCollectionLayout(self, request),
        'title': _("Activities")
    }


def get_activity_form_class(model, request):
    if isinstance(model, VacationActivityCollection):
        model = VacationActivity()

    return model.with_content_extensions(VacationActivityForm, request)


@FeriennetApp.form(model=VacationActivityCollection, template='form.pt',
                   form=get_activity_form_class, permission=Public, name='neu')
def handle_new_activity(self, request, form):

    if form.submitted(request):
        activity = self.add(
            title=form.title.data,
            user=request.current_user)

        # TODO redirect user to preview, then create a ticket
        form.populate_obj(activity)

        return morepath.redirect(request.link(self))

    return {
        'layout': NewVacationActivityLayout(self, request),
        'title': _("New Activity"),
        'form': form
    }
