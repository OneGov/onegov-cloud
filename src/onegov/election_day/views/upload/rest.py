from __future__ import annotations

import transaction

from base64 import b64decode
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_ech
from onegov.election_day.formats import import_election_compound_internal
from onegov.election_day.formats import import_election_internal_majorz
from onegov.election_day.formats import import_election_internal_proporz
from onegov.election_day.formats import import_party_results_internal
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.forms import UploadRestForm
from onegov.election_day.models import Principal
from onegov.election_day.models import UploadToken
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import Vote
from onegov.election_day.views.upload import set_locale
from onegov.election_day.views.upload import translate_errors
from onegov.election_day.views.upload import unsupported_year_error
from sqlalchemy import or_
from webob.exc import HTTPUnauthorized


from typing import cast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.core.types import RenderData
    from onegov.election_day.formats.imports.common import FileImportError
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


def authenticate(request: ElectionDayRequest) -> None:
    try:
        token = b64decode(
            request.authorization[1]  # type:ignore
        ).decode('utf-8').split(':')[1]

        request.session.query(UploadToken).filter_by(token=token).one()
    except Exception as exception:
        raise HTTPUnauthorized() from exception


@ElectionDayApp.json(
    model=Principal,
    name='upload',
    permission=Public,
    request_method='POST'
)
def view_upload_rest(
    self: Canton | Municipality,
    request: ElectionDayRequest
) -> RenderData:

    """ Upload election or vote results via REST using the internal format.

    Example usage:
        curl http://wahlen-abstimmungen.onegovcloud.ch/upload \
            --include \
            --user :<token> \
            --header "Accept-Language: de_CH" \
            --form "type=vote" \
            --form "id=vote-against-something" \
            --form "results=@results.csv"

    """
    set_locale(request)
    authenticate(request)

    status_code: int | None = None

    @request.after
    def set_status_code(response: Response) -> None:
        if status_code is not None:
            response.status_code = status_code

    errors: dict[str, list[FileImportError | str]] = {}

    form = request.get_form(UploadRestForm, model=self, csrf_support=False)
    try:
        valid = form.validate()
    except TypeError:
        valid = False

        if (isinstance(form.type.data, str) and
                form.type.data.startswith('FieldStorage')):
            form.type.errors = [*form.type.errors, _(
                'A file was submitted instead of a string. '
                'Use --form "type=xml" instead of --form "type=@file"'
            )]

    if not valid:
        status_code = 400
        return {
            'status': 'error',
            'errors': {
                key: [{'message': v} for v in value]
                for key, value in form.errors.items()
            }
        }

    # Check the ID
    session = request.session
    item: Election | ElectionCompound | Vote | None = None
    if form.type.data == 'vote':
        item = session.query(Vote).filter(
            or_(
                Vote.id == form.id.data,
                Vote.external_id == form.id.data,
            )
        ).first()
        if item is None:
            errors.setdefault('id', []).append(_('Invalid id'))
    elif form.type.data in ('election', 'parties'):
        item = session.query(ElectionCompound).filter(
            or_(
                ElectionCompound.id == form.id.data,
                ElectionCompound.external_id == form.id.data,
            )
        ).first()
        if item is None:
            item = session.query(Election).filter(
                or_(
                    Election.id == form.id.data,
                    Election.external_id == form.id.data,
                )
            ).first()
        if item is None:
            errors.setdefault('id', []).append(_('Invalid id'))

    # Check the type
    if item is not None and form.type.data == 'parties':
        if not isinstance(item, (ElectionCompound, ProporzElection)):
            errors.setdefault('id', []).append(
                _('Use an election based on proportional representation')
            )

    # Check if the year is supported
    if item is not None:
        if not self.is_year_available(item.date.year, False):
            errors.setdefault('id', []).append(
                unsupported_year_error(item.date.year)
            )

    if not errors:
        assert form.results.data is not None
        file = form.results.file
        assert file is not None
        mimetype = form.results.data['mimetype']

        err = []
        updated: Collection[Election | ElectionCompound | Vote]
        # NOTE: Technically item should only be none for type xml
        #       which in turn replaces this list but it's better
        #       to be safe than sorry
        updated = [item] if item is not None else []
        deleted: Collection[Election | ElectionCompound | Vote] = []
        if form.type.data == 'vote':
            item = cast('Vote', item)
            err = import_vote_internal(item, self, file, mimetype)
        elif form.type.data == 'election':
            if isinstance(item, ElectionCompound):
                err = import_election_compound_internal(
                    item, self, file, mimetype
                )
            elif isinstance(item, ProporzElection):
                err = import_election_internal_proporz(
                    item, self, file, mimetype
                )
            else:
                item = cast('Election', item)
                err = import_election_internal_majorz(
                    item, self, file, mimetype
                )
        elif form.type.data == 'parties':
            item = cast('ElectionCompound | ProporzElection', item)
            assert request.app.default_locale
            err = import_party_results_internal(
                item,
                request.app.principal,
                file,
                mimetype,
                request.app.locales,
                request.app.default_locale
            )
        elif form.type.data == 'xml':
            assert request.app.default_locale
            err, updated, deleted = import_ech(
                request.app.principal,
                file,
                session,
                request.app.default_locale
            )
        else:
            raise AssertionError(
                "Unexpected form.type.data; expected one of "
                "'vote', 'election', 'parties', or 'xml'."
            )
        if err:
            errors.setdefault('results', []).extend(err)

        if not errors:
            archive = ArchivedResultCollection(session)
            for item in updated:
                archive.update(item, request)
                if isinstance(item, ElectionCompound):
                    for election in item.elections:
                        archive.update(election, request)
                request.app.send_zulip(
                    self.name,
                    'New results available: [{}]({})'.format(
                        item.title, request.link(item)
                    )
                )
            for item in deleted:
                archive.delete(item, request)

    translate_errors(errors, request)

    if errors:
        status_code = 400
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.flush()
        return {'status': 'success', 'errors': {}}
