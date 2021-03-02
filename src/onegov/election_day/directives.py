from morepath.directive import HtmlAction
from morepath.directive import ViewAction
from morepath.request import Response
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.custom import json
from onegov.core.directives import HtmlHandleFormAction
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.election_day.forms import EmptyForm


class ManageHtmlAction(HtmlAction):

    """ HTML directive for manage views which makes sure the permission is set
    to private.

    """

    def __init__(self, model, **kwargs):
        kwargs['permission'] = Private
        super().__init__(model, **kwargs)


class ManageFormAction(HtmlHandleFormAction):

    """ HTML directive for manage forms which makes sure the permission is set
    to private. Sets a valid default for the template and form class.

    """

    def __init__(self, model, **kwargs):
        kwargs['permission'] = Private
        kwargs['template'] = kwargs.get('template', 'form.pt')
        kwargs['form'] = kwargs.get('form', EmptyForm)
        super().__init__(model, **kwargs)


class SvgFileViewAction(ViewAction):

    """ View directive for viewing SVG files from filestorage. The SVGs
    are created using a cronjob and might not be available. """

    def __init__(self, model, **kwargs):
        kwargs['permission'] = kwargs.get('permission', Public)
        kwargs['render'] = self.render
        super().__init__(model, **kwargs)

    @staticmethod
    def render(content, request):
        path = content.get('path')
        name = content.get('name')
        if not path:
            return Response(status='503 Service Unavailable')

        content = None
        with request.app.filestorage.open(path, 'r') as f:
            content = f.read()

        return Response(
            content,
            content_type='application/svg; charset=utf-8',
            content_disposition=f'inline; filename={name}'
        )


class PdfFileViewAction(ViewAction):

    """ View directive for viewing PDF files from filestorage. The PDFs
    are created using a cronjob and might not be available. """

    def __init__(self, model, **kwargs):
        kwargs['permission'] = kwargs.get('permission', Public)
        kwargs['render'] = self.render
        super().__init__(model, **kwargs)

    @staticmethod
    def render(content, request):
        path = content.get('path')
        name = content.get('name')
        if not path:
            return Response(status='503 Service Unavailable')

        content = None
        with request.app.filestorage.open(path, 'rb') as f:
            content = f.read()

        return Response(
            content,
            content_type='application/pdf',
            content_disposition=f'inline; filename={name}.pdf'
        )


class JsonFileAction(ViewAction):

    """ View directive for viewing JSON data as file. """

    def __init__(self, model, **kwargs):
        kwargs['permission'] = kwargs.get('permission', Public)
        kwargs['render'] = self.render
        super().__init__(model, **kwargs)

    @staticmethod
    def render(content, request):
        data = content.get('data', {})
        name = content.get('name', 'data.json')
        return Response(
            json.dumps(data, sort_keys=True, indent=2).encode('utf-8'),
            content_type='application/json',
            content_disposition=f'inline; filename={name}.json')


class CsvFileAction(ViewAction):

    """ View directive for viewing CSV data as file. """

    def __init__(self, model, **kwargs):
        kwargs['permission'] = kwargs.get('permission', Public)
        kwargs['render'] = self.render
        super().__init__(model, **kwargs)

    @staticmethod
    def render(content, request):
        data = content.get('data', {})
        name = content.get('name', 'data.json')
        return Response(
            convert_list_of_dicts_to_csv(data),
            content_type='text/csv',
            content_disposition=f'inline; filename={name}.csv'
        )
