from onegov.core.utils import normalize_for_url
from morepath.request import Response
from onegov.agency import AgencyApp
from onegov.agency.utils import export_to_xlsx
from onegov.core.security import Private
from onegov.org.models import Organisation


@AgencyApp.view(
    model=Organisation,
    permission=Private,
    name='export-agencies'
)
def view_export(self, request):

    response = Response(
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition='inline; filename={}.xlsx'.format(
            normalize_for_url(self.name)
        )
    )
    export_to_xlsx(request, response.body_file)
    return response
