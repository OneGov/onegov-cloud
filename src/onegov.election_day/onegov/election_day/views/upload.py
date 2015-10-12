""" The upload view. """

from onegov.ballot import Ballot, BallotResult, Vote
from onegov.core.csv import CSVFile
from onegov.core.errors import (
    AmbiguousColumnsError,
    DuplicateColumnNames,
    EmptyFile,
    InvalidFormat,
    MissingColumnsError,
)
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import UploadForm
from onegov.election_day.layout import ManageLayout
from onegov.election_day.models import Manage
from sqlalchemy.orm import object_session


BALLOT_TYPES = {'proposal', 'counter-proposal', 'tie-breaker'}


class FileImportError(object):
    __slots__ = ['line', 'error']

    def __init__(self, line, error):
        self.line = line
        self.error = error


def import_file(vote, ballot_type, file, mimetype):
    """ Tries to import the given csv, xls or xlsx file to the given ballot
    result type.

    :return: A dictionary containing the status and a list of errors if any.
    For example::

        {'status': 'ok', 'errors': []}
        {'status': 'fail': 'errors': ['x on line y is z']}

    """
    assert ballot_type in BALLOT_TYPES

    if mimetype == 'text/plain':
        csvfile = file

    try:
        csv = CSVFile(csvfile, expected_headers=[
            'Bezirk',
            'BFS Nummer',
            'Gemeinde',
            'Ja Stimmen',
            'Nein Stimmen',
            'Stimmberechtigte',
            'Leere Stimmzettel',
            'Ungültige Stimmzettel'
        ])
    except MissingColumnsError as e:
        return {'status': 'error', 'errors': [
            FileImportError(None, _("Missing columns: '${cols}'", mapping={
                'cols': ', '.join(e.columns)
            }))
        ]}
    except AmbiguousColumnsError as e:
        return {'status': 'error', 'errors': [
            FileImportError(None, _(
                "Could not find the expected columns, "
                "make sure all required columns exist and that there are no "
                "extra columns."
            ))
        ]}
    except AmbiguousColumnsError as e:
        return {'status': 'error', 'errors': [
            FileImportError(None, _(
                "Could not find the expected columns, "
                "make sure all required columns exist and that there are no "
                "extra columns."
            ))
        ]}
    except DuplicateColumnNames as e:
        return {'status': 'error', 'errors': [
            FileImportError(None, _("Some column names appear twice."))
        ]}
    except InvalidFormat as e:
        return {'status': 'error', 'errors': [
            FileImportError(None, _("Not a valid csv/xls/xlsx file."))
        ]}
    except EmptyFile as e:
        return {'status': 'error', 'errors': [
            FileImportError(None, _("The csv/xls/xlsx file is empty."))
        ]}

    ballot = next((b for b in vote.ballots if b.type == ballot_type), None)

    if not ballot:
        ballot = Ballot(type=ballot_type)
        vote.ballots.append(ballot)

    ballot_results = []
    errors = []

    existing_municipality_ids = set()
    existing_groups = set()

    for line in csv.lines:
        line_errors = []

        # the name of the municipality
        group = '/'.join(p for p in (line.bezirk, line.gemeinde) if p)

        if not group.strip().replace('/', ''):
            line_errors.append(_("Missing municipality"))

        if group in existing_groups:
            line_errors.append(_("${group} was found twice"), mapping={
                'group': group
            })

        existing_groups.add(group)

        # the id of the municipality
        try:
            municipality_id = int(line.bfs_nummer or 0)
        except ValueError:
            line_errors.append(_("Invalid municipality id"))
        else:
            if municipality_id in existing_municipality_ids:
                line_errors.append(
                    _("municipality id ${id} was found twice"), mapping={
                        'id': municipality_id
                    }
                )

            existing_municipality_ids.add(municipality_id)

        # the yeas
        try:
            yeas = int(line.ja_stimmen or 0)
        except ValueError:
            line_errors.append(_("Could not read yeas"))

        # the nays
        try:
            nays = int(line.nein_stimmen or 0)
        except ValueError:
            line_errors.append(_("Could not read nays"))

        # the elegible voters
        try:
            elegible_voters = int(line.stimmberechtigte or 0)
        except ValueError:
            line_errors.append(_("Could not read the elegible voters"))

        # the empty votes
        try:
            empty = int(line.leere_stimmzettel or 0)
        except ValueError:
            line_errors.append(_("Could not read the empty votes"))

        # the invalid votes
        try:
            invalid = int(line.ungultige_stimmzettel or 0)
        except ValueError:
            line_errors.append(_("Could not read the invalid votes"))

        # now let's do some sanity checks
        if (yeas + nays + empty + invalid) > elegible_voters:
            line_errors.append(_("More cast votes than elegible voters"))

        if not elegible_voters:
            line_errors.append(_("No elegible voters"))

        # pass the errors
        if line_errors:
            errors.extend(
                FileImportError(line=line.rownumber, error=err)
                for err in line_errors
            )
            continue

        # all went well (only keep doing this as long as there are no errors)
        if not errors:
            ballot_results.append(
                BallotResult(
                    group=group,
                    counted=True,
                    yeas=yeas,
                    nays=nays,
                    elegible_voters=elegible_voters,
                    municipality_id=municipality_id,
                    empty=empty,
                    invalid=invalid
                )
            )

    if not errors and not ballot_results:
        errors.append(FileImportError(line=None, error=_("No data found")))

    if errors:
        return {'status': 'fail', 'errors': errors}

    if ballot_results:
        session = object_session(vote)
        for result in ballot.results:
            session.delete(result)
        for result in ballot_results:
            ballot.results.append(result)

    return {'status': 'ok', 'errors': errors}


def get_form_class(vote, request):
    if not vote.ballots:
        return UploadForm

    class LimitedUploadForm(UploadForm):
        pass

    if len(vote.ballots) == 1:
        LimitedUploadForm.type.kwargs['default'] = 'simple'
        LimitedUploadForm.type.kwargs['choices'] = [
            ('simple', _("Simple Vote"))
        ]
    else:
        LimitedUploadForm.type.kwargs['default'] = 'complex'
        LimitedUploadForm.type.kwargs['choices'] = [
            ('complex', _("Vote with Counter-Proposal"))
        ]

    return LimitedUploadForm


@ElectionDayApp.form(model=Vote, name='upload', template='upload.pt',
                     permission=Private, form=UploadForm)
def view_upload(self, request, form):

    results = {}

    # if the vote already has results, do not give the user the choice to
    # switch between the different ballot types
    if self.counter_proposal:
        form.type.choices = form.type.choices[1:]
        form.type.data = 'complex'
    elif self.proposal:
        form.type.choices = form.type.choices[:1]
        form.type.data = 'simple'

    if form.submitted(request):
        if form.data['type'] == 'simple':
            ballot_types = ('proposal', )
        else:
            ballot_types = BALLOT_TYPES

        for ballot_type in ballot_types:
            field = getattr(form, ballot_type.replace('-', '_'))

            results[ballot_type] = import_file(
                self, ballot_type,
                field.raw_data[0].file,
                field.data['mimetype']
            )

    if results:
        if all(r['status'] == 'ok' for r in results.values()):
            status = 'success'
        else:
            status = 'error'
    else:
        status = 'open'

    return {
        'layout': ManageLayout(self, request),
        'title': self.title,
        'subtitle': _("Upload results"),
        'form': form,
        'cancel': request.link(Manage(request.app.session())),
        'results': results,
        'status': status,
        'vote': self
    }
