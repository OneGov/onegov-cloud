import base64

from onegov.core.security import Public
from onegov.winterthur import WinterthurApp
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.org.layout import GeneralFileCollectionLayout


@WinterthurApp.html(
    model=GeneralFileCollection,
    name='shift-schedule',
    permission=Public,
    template='shift_schedule.pt'
)
def view_shift_schedule(self, request, layout=None):
    layout = layout or GeneralFileCollectionLayout(self, request)
    session = request.session
    file_link = ""

    files = GeneralFileCollection(session).query().order_by(
        GeneralFile.created
    ).filter(GeneralFile.published)
    files = files.all()
    if files:
        file = files[-1]

        if file.claimed_extension == 'pdf':
            img_buffer = request.app.get_shift_schedule_image(file)
            str_equivalent_image = base64.b64encode(img_buffer.getvalue(
            )).decode()
            file_link = f'data:image/png;base64,{str_equivalent_image}'

    return {
        'title': "Schichtplan",
        'layout': layout,
        'file_path': file_link,
        'model': self
    }
