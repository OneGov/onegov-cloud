from onegov.core.security import Private
from onegov.winterthur import WinterthurApp
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.org.layout import GeneralFileCollectionLayout

# from onegov.file.utils import extension_for_content_type


@WinterthurApp.html(
    model=GeneralFileCollection,
    name='shift-schedule',
    permission=Private,
    template='shift_schedule.pt'
)
def view_shift_schedule(self, request, layout=None):
    layout = layout or GeneralFileCollectionLayout(self, request)
    session = request.session
    # extension = extension_for_content_type(
    #     file.content_type,
    #     file.name
    # )

    files = GeneralFileCollection(session).query().order_by(
        GeneralFile.created
    )
    files = files.all()
    file = files[-1]

    return {
        'title': "Schichtplan",
        'layout': layout,
        'file': file,
        'extension': file.claimed_extension,
        'count': len(files),
        'model': self
    }
