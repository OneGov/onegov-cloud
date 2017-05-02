""" The upload view. """
import morepath
import transaction

from onegov.ballot import Election
from onegov.core.security import Private
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_election_internal
from onegov.election_day.formats import import_election_sesam
from onegov.election_day.formats import import_election_wabsti_majorz
from onegov.election_day.formats import import_election_wabsti_proporz
from onegov.election_day.formats import import_election_wabstic_majorz
from onegov.election_day.formats import import_election_wabstic_proporz
from onegov.election_day.formats import import_party_results
from onegov.election_day.forms import UploadElectionPartyResultsForm
from onegov.election_day.forms import UploadMajorzElectionForm
from onegov.election_day.forms import UploadProporzElectionForm
from onegov.election_day.layout import ManageElectionsLayout
from onegov.election_day.views.upload import unsupported_year_error


@ElectionDayApp.html(model=Election, name='upload', permission=Private)
def view_upload_election(self, request):
    if self.type == 'majorz':
        return morepath.redirect(request.link(self, 'upload-majorz'))
    return morepath.redirect(request.link(self, 'upload-proporz'))


@ElectionDayApp.form(model=Election, name='upload-majorz',
                     template='upload_election.pt', permission=Private,
                     form=UploadMajorzElectionForm)
def view_upload_majorz_election(self, request, form):

    assert self.type == 'majorz'

    errors = []

    form.adjust(request.app.principal, self)

    status = 'open'
    if form.submitted(request):
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, map_required=False):
            errors = [unsupported_year_error(self.date.year)]
        else:
            entities = principal.entities[self.date.year]
            if form.file_format.data == 'internal':
                errors = import_election_internal(
                    entities, self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype']
                )
            elif form.file_format.data == 'sesam':
                errors = import_election_sesam(
                    entities, self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype']
                )
                self.absolute_majority = form.majority.data
            elif form.file_format.data == 'wabsti':
                elected = len(form.elected.data)
                errors = import_election_wabsti_majorz(
                    entities, self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype'],
                    form.elected.raw_data[0].file if elected else None,
                    form.elected.data['mimetype'] if elected else None,
                )
                self.absolute_majority = form.majority.data
                self.status = 'final' if form.complete.data else 'interim'
            elif form.file_format.data == 'wabsti_c':
                for source in self.data_sources:
                    errors.extend(
                        import_election_wabstic_majorz(
                            self,
                            source.district,
                            source.number,
                            entities,
                            form.wm_wahl.raw_data[0].file,
                            form.wm_wahl.data['mimetype'],
                            form.wmstatic_gemeinden.raw_data[0].file,
                            form.wmstatic_gemeinden.data['mimetype'],
                            form.wm_gemeinden.raw_data[0].file,
                            form.wm_gemeinden.data['mimetype'],
                            form.wm_kandidaten.raw_data[0].file,
                            form.wm_kandidaten.data['mimetype'],
                            form.wm_kandidatengde.raw_data[0].file,
                            form.wm_kandidatengde.data['mimetype']
                        )
                    )
            else:
                raise NotImplementedError("Unsupported import format")

            archive = ArchivedResultCollection(request.app.session())
            archive.update(self, request)

            if errors:
                status = 'error'
                transaction.abort()
            else:
                status = 'success'
                request.app.pages_cache.invalidate()
                request.app.send_hipchat(
                    request.app.principal.name,
                    'New results available: <a href="{}">{}</a>'.format(
                        request.link(self), self.title
                    )
                )

    layout = ManageElectionsLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
        'election': self
    }


@ElectionDayApp.form(model=Election, name='upload-proporz',
                     template='upload_election.pt', permission=Private,
                     form=UploadProporzElectionForm)
def view_upload(self, request, form):

    assert self.type == 'proporz'

    errors = []

    form.adjust(request.app.principal, self)

    status = 'open'
    if form.submitted(request):
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, map_required=False):
            errors = [unsupported_year_error(self.date.year)]
        else:
            entities = principal.entities[self.date.year]
            if form.file_format.data == 'internal':
                errors = import_election_internal(
                    entities, self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype']
                )
            elif form.file_format.data == 'sesam':
                errors = import_election_sesam(
                    entities, self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype']
                )
            elif form.file_format.data == 'wabsti':
                connections = len(form.connections.data)
                stats = len(form.statistics.data)
                elected = len(form.elected.data)
                errors = import_election_wabsti_proporz(
                    entities, self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype'],
                    form.connections.raw_data[0].file if connections else None,
                    form.connections.data['mimetype'] if connections else None,
                    form.elected.raw_data[0].file if elected else None,
                    form.elected.data['mimetype'] if elected else None,
                    form.statistics.raw_data[0].file if stats else None,
                    form.statistics.data['mimetype'] if stats else None
                )
                self.status = 'final' if form.complete.data else 'interim'
            elif form.file_format.data == 'wabsti_c':
                for source in self.data_sources:
                    errors.extend(
                        import_election_wabstic_proporz(
                            self,
                            source.district,
                            source.number,
                            entities,
                            form.wp_wahl.raw_data[0].file,
                            form.wp_wahl.data['mimetype'],
                            form.wpstatic_gemeinden.raw_data[0].file,
                            form.wpstatic_gemeinden.data['mimetype'],
                            form.wp_gemeinden.raw_data[0].file,
                            form.wp_gemeinden.data['mimetype'],
                            form.wp_listen.raw_data[0].file,
                            form.wp_listen.data['mimetype'],
                            form.wp_listengde.raw_data[0].file,
                            form.wp_listengde.data['mimetype'],
                            form.wpstatic_kandidaten.raw_data[0].file,
                            form.wpstatic_kandidaten.data['mimetype'],
                            form.wp_kandidaten.raw_data[0].file,
                            form.wp_kandidaten.data['mimetype'],
                            form.wp_kandidatengde.raw_data[0].file,
                            form.wp_kandidatengde.data['mimetype'],
                        )
                    )
            else:
                raise NotImplementedError("Unsupported import format")

            archive = ArchivedResultCollection(request.app.session())
            archive.update(self, request)

            if errors:
                status = 'error'
                transaction.abort()
            else:
                status = 'success'
                request.app.pages_cache.invalidate()
                request.app.send_hipchat(
                    request.app.principal.name,
                    'New results available: <a href="{}">{}</a>'.format(
                        request.link(self), self.title
                    )
                )

    layout = ManageElectionsLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
        'election': self
    }


@ElectionDayApp.form(model=Election, name='upload-party-results',
                     template='upload_election.pt', permission=Private,
                     form=UploadElectionPartyResultsForm)
def view_party_results_upload(self, request, form):

    errors = []

    status = 'open'
    if form.submitted(request):
        errors = import_party_results(
            self,
            form.parties.raw_data[0].file,
            form.parties.data['mimetype']
        )

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            request.app.pages_cache.invalidate()

    layout = ManageElectionsLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
        'election': self
    }
