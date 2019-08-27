""" Lists the custom forms. """

from onegov.core.security import Public
from onegov.form import FormCollection, FormDefinition
from onegov.org import _, OrgApp
from onegov.org.layout import FormCollectionLayout
from onegov.org.utils import group_by_column


@OrgApp.html(model=FormCollection, template='forms.pt', permission=Public)
def view_form_collection(self, request):

    return {
        'layout': FormCollectionLayout(self, request),
        'title': _("Forms"),
        'forms': group_by_column(
            request=request,
            query=self.definitions.query(),
            group_column=FormDefinition.group,
            sort_column=FormDefinition.order
        )
    }
