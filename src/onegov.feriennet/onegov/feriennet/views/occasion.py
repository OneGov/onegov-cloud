from onegov.activity import Occasion, OccasionCollection
from onegov.core.security import Private
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.forms.occasion import OccasionForm
from onegov.feriennet.layout import OccasionFormLayout
from onegov.feriennet.models import VacationActivity


@FeriennetApp.form(
    model=VacationActivity,
    template='form.pt',
    form=OccasionForm,
    permission=Private,
    name='neue-durchfuehrung')
def new_occasion(self, request, form):

    if form.submitted(request):
        occasions = OccasionCollection(request.app.session())
        form.populate_obj(occasions.add(
            activity=self,
            start=form.start.data,
            end=form.end.data,
            timezone=form.timezone
        ))

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    return {
        'layout': OccasionFormLayout(self, request, _("New Occasion")),
        'title': _("New Occasion"),
        'form': form
    }


@FeriennetApp.form(
    model=Occasion,
    template='form.pt',
    form=OccasionForm,
    permission=Private,
    name='bearbeiten')
def edit_occasion(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.activity))

    elif not request.POST:
        form.process(obj=self)

    return {
        'layout': OccasionFormLayout(
            self.activity, request, _("Edit Occasion")),
        'title': _("Edit Occasion"),
        'form': form
    }


@FeriennetApp.view(
    model=Occasion,
    permission=Private,
    request_method='DELETE')
def delete_occasion(self, request):
    request.assert_valid_csrf_token()

    OccasionCollection(request.app.session()).delete(self)
