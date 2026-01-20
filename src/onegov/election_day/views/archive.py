from __future__ import annotations

from fs.errors import ResourceNotFound
from morepath.request import Response
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import SearchableArchivedResultCollection
from onegov.election_day.forms import ArchiveSearchFormElection
from onegov.election_day.forms import ArchiveSearchFormVote
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts.archive import ArchiveLayout
from onegov.election_day.models import Principal
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_summaries
from webob.exc import HTTPNotFound


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.html(
    model=ArchivedResultCollection,
    template='archive.pt',
    permission=MaybePublic
)
def view_archive(
    self: ArchivedResultCollection,
    request: ElectionDayRequest
) -> RenderData:
    """ Shows all the results from the elections and votes for a given year
    or date.

    """

    layout = DefaultLayout(self, request)
    results, _ = self.by_date()

    return {
        'layout': layout,
        'date': self.date,
        'archive_items': self.group_items(results, request),
    }


@ElectionDayApp.json(
    model=ArchivedResultCollection,
    name='json',
    permission=MaybePublic
)
def view_archive_json(
    self: ArchivedResultCollection,
    request: ElectionDayRequest
) -> JSON_ro:
    """ Shows all the results from the elections and votes for a given year
    or date as JSON.

    """

    results, last_modified = self.by_date()

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    return {
        'canton': request.app.principal.id,
        'name': request.app.principal.name,
        'results': get_summaries(results, request),
        'archive': {
            str(year): request.link(self.for_date(str(year)))
            for year in self.get_years()
        }
    }


@ElectionDayApp.html(
    model=Principal,
    template='archive.pt',
    permission=MaybePublic
)
def view_principal(
    self: Principal,
    request: ElectionDayRequest
) -> RenderData:
    """ Shows all the results from the elections and votes of the last election
    day. It's the landing page.

    """

    layout = DefaultLayout(self, request)
    archive = ArchivedResultCollection(request.session)
    current, _ = archive.current()

    return {
        'layout': layout,
        'archive_items': archive.group_items(current, request),
        'date': None,
    }


@ElectionDayApp.json(
    model=Principal,
    name='json',
    permission=MaybePublic
)
def view_principal_json(
    self: Principal,
    request: ElectionDayRequest
) -> JSON_ro:
    """ Shows all the results from the elections and votes of the last election
    day as JSON.

    """

    archive = ArchivedResultCollection(request.session)
    current, last_modified = archive.current()

    @request.after
    def add_headers(response: Response) -> None:
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    return {
        'canton': self.id,
        'name': self.name,
        'results': get_summaries(current, request),
        'archive': {
            str(year): request.link(archive.for_date(str(year)))
            for year in archive.get_years()
        }
    }


def search_form(
    model: SearchableArchivedResultCollection,
    request: ElectionDayRequest,
    form: None = None
) -> type[ArchiveSearchFormVote | ArchiveSearchFormElection]:

    if model.item_type == 'vote':
        return ArchiveSearchFormVote
    return ArchiveSearchFormElection


@ElectionDayApp.form(
    model=SearchableArchivedResultCollection,
    template='archive_search.pt',
    form=search_form,
    permission=MaybePublic,
)
def view_archive_search(
    self: SearchableArchivedResultCollection,
    request: ElectionDayRequest,
    form: ArchiveSearchFormVote | ArchiveSearchFormElection
) -> RenderData:
    """ Shows all the results from the elections and votes of the last election
    day. It's the landing page.
    """

    layout = ArchiveLayout(self, request)
    if request.locale:
        self.locale = request.locale

    if not form.errors:
        form.apply_model(self)

    return {
        'item_type': self.item_type,
        'layout': layout,
        'form': form,
        'form_method': 'GET',
        'item_count': self.subset_count,
        'results': self.batch
    }


@ElectionDayApp.view(
    model=Principal,
    name='archive-download',
    permission=MaybePublic
)
def view_archive_download(
    self: Principal,
    request: ElectionDayRequest
) -> Response:

    filestorage = request.app.filestorage
    assert filestorage is not None

    if not filestorage.isdir('archive'):
        raise HTTPNotFound()
    try:
        zip_dir = filestorage.opendir('archive/zip')
        content = None
        with zip_dir.open('archive.zip', mode='rb') as zipfile:
            content = zipfile.read()
        if not content:
            raise HTTPNotFound()
        return Response(
            content,
            content_type='application/zip',
            content_disposition='inline; filename=Archive.zip'
        )
    except (FileNotFoundError, ResourceNotFound) as exception:
        raise HTTPNotFound() from exception
