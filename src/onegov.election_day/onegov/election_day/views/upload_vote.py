""" The upload view. """
import transaction

from onegov.ballot import Ballot, BallotResult, Vote
from onegov.core.csv import CSVFile, convert_xls_to_csv
from onegov.core.errors import (
    AmbiguousColumnsError,
    DuplicateColumnNamesError,
    EmptyFileError,
    EmptyLineInFileError,
    InvalidFormatError,
    MissingColumnsError,
)
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.layout import ManageLayout
from onegov.election_day.models import Manage
from onegov.election_day.utils import FileImportError
from sqlalchemy.orm import object_session


BALLOT_TYPES = {'proposal', 'counter-proposal', 'tie-breaker'}


def import_file(principal, vote, ballot_type, file, mimetype):
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
    else:
        try:
            csvfile = convert_xls_to_csv(file, 'Resultate')
        except IOError:
            csvfile = convert_xls_to_csv(file)

    if not principal.is_year_available(vote.date.year):
        return {'status': 'error', 'errors': [
            FileImportError(_("The year ${year} is not yet supported",
                mapping={'year': vote.date.year}
            ))
        ]}

    municipalities = principal.municipalities[vote.date.year]

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
            FileImportError(_("Missing columns: '${cols}'", mapping={
                'cols': ', '.join(e.columns)
            }))
        ]}
    except AmbiguousColumnsError as e:
        return {'status': 'error', 'errors': [
            FileImportError(_(
                "Could not find the expected columns, "
                "make sure all required columns exist and that there are no "
                "extra columns."
            ))
        ]}
    except DuplicateColumnNamesError as e:
        return {'status': 'error', 'errors': [
            FileImportError(_("Some column names appear twice."))
        ]}
    except InvalidFormatError as e:
        return {'status': 'error', 'errors': [
            FileImportError(_("Not a valid csv/xls/xlsx file."))
        ]}
    except EmptyFileError as e:
        return {'status': 'error', 'errors': [
            FileImportError(_("The csv/xls/xlsx file is empty."))
        ]}
    except EmptyLineInFileError as e:
        return {'status': 'error', 'errors': [
            FileImportError(_("The file contains an empty line."))
        ]}

    ballot = next((b for b in vote.ballots if b.type == ballot_type), None)

    if not ballot:
        ballot = Ballot(type=ballot_type)
        vote.ballots.append(ballot)

    ballot_results = []
    errors = []

    added_municipality_ids = set()
    added_groups = set()

    # if we have the value "unknown" or "unbekannt" in any of the following
    # colums, we ignore the whole line
    significant_columns = (
        'ja_stimmen',
        'leere_stimmzettel',
        'nein_stimmen',
        'stimmberechtigte',
        'ungultige_stimmzettel',
    )

    skip_indicators = ('unknown', 'unbekannt')

    def skip_line(line):
        for column in significant_columns:
            if str(getattr(line, column, '')).lower() in skip_indicators:
                return True

        return False

    skipped = 0

    for line in csv.lines:

        if skip_line(line):
            skipped += 1
            continue

        line_errors = []

        # the name of the municipality
        group = '/'.join(p for p in (line.bezirk, line.gemeinde) if p)

        if not group.strip().replace('/', ''):
            line_errors.append(_("Missing municipality"))

        if group in added_groups:
            line_errors.append(_("${group} was found twice", mapping={
                'group': group
            }))

        added_groups.add(group)

        # the id of the municipality
        try:
            municipality_id = int(line.bfs_nummer or 0)
        except ValueError:
            line_errors.append(_("Invalid municipality id"))
        else:
            if municipality_id in added_municipality_ids:
                line_errors.append(
                    _("municipality id ${id} was found twice", mapping={
                        'id': municipality_id
                    }))

            if municipality_id not in municipalities:
                line_errors.append(
                    _("municipality id ${id} is unknown", mapping={
                        'id': municipality_id
                    }))
            else:
                added_municipality_ids.add(municipality_id)

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
        try:
            if not elegible_voters:
                line_errors.append(_("No elegible voters"))

            if (yeas + nays + empty + invalid) > elegible_voters:
                line_errors.append(_("More cast votes than elegible voters"))

        except UnboundLocalError:
            pass

        # pass the errors
        if line_errors:
            errors.extend(
                FileImportError(error=err, line=line.rownumber)
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

    if not errors and not ballot_results and not skipped:
        errors.append(FileImportError(_("No data found")))

    if not errors:
        for id in (municipalities.keys() - added_municipality_ids):
            municipality = municipalities[id]

            ballot_results.append(
                BallotResult(
                    group='/'.join(p for p in (
                        municipality.get('district'),
                        municipality['name']
                    ) if p is not None),
                    counted=False,
                    municipality_id=id
                )
            )

    if errors:
        return {'status': 'fail', 'errors': errors, 'records': 0}

    if ballot_results:
        session = object_session(vote)
        for result in ballot.results:
            session.delete(result)
        for result in ballot_results:
            ballot.results.append(result)

    return {
        'status': 'ok',
        'errors': errors,
        'records': len(added_municipality_ids)
    }


def get_form_class(vote, request):
    if not vote.ballots:
        return UploadVoteForm

    class LimitedUploadVoteForm(UploadVoteForm):
        pass

    if len(vote.ballots) == 1:
        LimitedUploadVoteForm.type.kwargs['default'] = 'simple'
        LimitedUploadVoteForm.type.kwargs['choices'] = [
            ('simple', _("Simple Vote"))
        ]
    else:
        LimitedUploadVoteForm.type.kwargs['default'] = 'complex'
        LimitedUploadVoteForm.type.kwargs['choices'] = [
            ('complex', _("Vote with Counter-Proposal"))
        ]

    return LimitedUploadVoteForm


@ElectionDayApp.form(model=Vote, name='upload', template='upload_vote.pt',
                     permission=Private, form=UploadVoteForm)
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
                request.app.principal,
                self,
                ballot_type,
                field.raw_data[0].file,
                field.data['mimetype']
            )

    if results:
        if all(r['status'] == 'ok' for r in results.values()):

            records = max(r['records'] for r in results.values())

            # make sure all imports have the same amount of records
            for result in results.values():
                if result['records'] < records:
                    result['status'] = 'error'
                    result['errors'].append(
                        FileImportError(
                            _("This ballot has fewer results than the others")
                        )
                    )
                    status = 'error'
                    break
            else:
                status = 'success'
        else:
            status = 'error'
    else:
        status = 'open'

    if status == 'error':
        transaction.abort()

    return {
        'layout': ManageLayout(self, request),
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Upload results"),
        'form': form,
        'cancel': request.link(Manage(request.app.session())),
        'results': results,
        'status': status,
        'vote': self
    }
