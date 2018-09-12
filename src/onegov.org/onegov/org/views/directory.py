import re
import transaction

from collections import namedtuple
from onegov.core.security import Public, Private, Secret
from onegov.core.utils import render_file
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryEntry
from onegov.directory import DirectoryEntryCollection
from onegov.directory import DirectoryZipArchive
from onegov.directory.errors import DuplicateEntryError
from onegov.directory.errors import MissingColumnError
from onegov.directory.errors import MissingFileError
from onegov.directory.errors import ValidationError
from onegov.file import File
from onegov.form import FormCollection, as_internal_id
from onegov.form.fields import UploadField
from onegov.org import OrgApp, _
from onegov.org.forms import DirectoryForm, DirectoryImportForm
from onegov.org.forms.generic import ExportForm
from onegov.org.layout import DirectoryCollectionLayout
from onegov.org.layout import DirectoryEntryCollectionLayout
from onegov.org.layout import DirectoryEntryLayout
from onegov.org.models import DirectorySubmissionAction
from onegov.org.models import ExtendedDirectory, ExtendedDirectoryEntry
from onegov.org.new_elements import Link
from purl import URL
from tempfile import NamedTemporaryFile
from webob.exc import HTTPForbidden


def get_directory_form_class(model, request):
    return ExtendedDirectory().with_content_extensions(DirectoryForm, request)


def get_directory_entry_form_class(model, request):
    form_class = ExtendedDirectoryEntry().with_content_extensions(
        model.directory.form_class, request)

    class OptionalMapForm(form_class):
        def on_request(self):
            if model.directory.enable_map == 'no':
                self.delete_field('coordinates')

    return OptionalMapForm


def get_submission_form_class(model, request):
    return model.directory.form_class_for_submissions


@OrgApp.html(
    model=DirectoryCollection,
    template='directories.pt',
    permission=Public)
def view_directories(self, request):
    return {
        'title': _("Directories"),
        'layout': DirectoryCollectionLayout(self, request),
        'directories': request.exclude_invisible(self.query()),
        'link': lambda directory: request.link(
            DirectoryEntryCollection(directory)
        )
    }


@OrgApp.view(
    model=Directory,
    permission=Public)
def view_directory_redirect(self, request):
    return request.redirect(request.class_link(
        DirectoryEntryCollection, {'directory_name': self.name}
    ))


@OrgApp.form(model=DirectoryCollection, name='new', template='form.pt',
             permission=Secret, form=get_directory_form_class)
def handle_new_directory(self, request, form):
    if form.submitted(request):
        directory = self.add_by_form(form, properties=('configuration', ))

        request.success(_("Added a new directory"))
        return request.redirect(
            request.link(DirectoryEntryCollection(directory)))

    layout = DirectoryCollectionLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Directories"), request.link(self)),
        Link(_("New"), request.link(self, name='new'))
    ]

    return {
        'layout': layout,
        'title': _("New Directory"),
        'form': form,
        'form_width': 'huge',
    }


@OrgApp.form(model=DirectoryEntryCollection, name='edit',
             template='directory_form.pt', permission=Secret,
             form=get_directory_form_class)
def handle_edit_directory(self, request, form):
    migration = None
    error = None

    if form.submitted(request):
        save_changes = True

        if self.directory.entries:
            migration = self.directory.migration(
                form.structure.data,
                form.configuration
            )

            if migration.changes:
                if not migration.possible:
                    save_changes = False
                    request.alert(_(
                        "The requested change cannot be performed, "
                        "as it is incompatible with existing entries"
                    ))
                else:
                    if not request.params.get('confirm'):
                        form.action += '&confirm=1'
                        save_changes = False

        if save_changes:
            form.populate_obj(self.directory)

            try:
                self.session.flush()
            except ValidationError as e:
                error = e
                error.link = request.class_link(DirectoryEntry, {
                    'directory_name': self.directory.name,
                    'name': e.entry.name
                })
                transaction.abort()
            else:
                request.success(_("Your changes were saved"))
                return request.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self.directory)

    layout = DirectoryCollectionLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Directories"), request.link(self)),
        Link(_(self.directory.title), request.link(self)),
        Link(_("Edit"), '#')
    ]

    return {
        'layout': layout,
        'title': self.directory.title,
        'form': form,
        'form_width': 'large',
        'migration': migration,
        'model': self,
        'error': error,
        'error_translate': lambda text: request.translate(_(text)),
        'directory': self.directory,
    }


@OrgApp.view(
    model=DirectoryEntryCollection,
    permission=Secret,
    request_method='DELETE')
def delete_directory(self, request):
    request.assert_valid_csrf_token()

    session = request.session

    for entry in self.directory.entries:
        session.delete(entry)

    DirectoryCollection(session).delete(self.directory)
    request.success(_("The directory was deleted"))


@OrgApp.html(
    model=DirectoryEntryCollection,
    permission=Public,
    template='directory.pt')
def view_directory(self, request):

    Filter = namedtuple('Filter', ('title', 'tags'))
    filters = []
    empty = tuple()

    radio_fields = set(
        f.id for f in self.directory.fields if f.type == 'radio'
    )

    for keyword, title, values in self.available_filters:
        filters.append(Filter(title=title, tags=tuple(
            Link(
                text=value,
                active=value in self.keywords.get(keyword, empty),
                url=request.link(self.for_filter(
                    singular=keyword in radio_fields,
                    **{keyword: value}
                )),
                rounded=keyword in radio_fields
            ) for value in values
        )))

    entries = request.exclude_invisible(self.query())

    if self.directory.configuration.thumbnail:
        thumbnail = as_internal_id(self.directory.configuration.thumbnail)
    else:
        thumbnail = None

    def thumbnail_link(entry):
        id = (entry.values.get(thumbnail) or {}).get('data', '').lstrip('@')
        return id and request.class_link(File, {'id': id}, name='thumbnail')

    return {
        'layout': DirectoryEntryCollectionLayout(self, request),
        'title': self.directory.title,
        'entries': entries,
        'directory': self.directory,
        'searchwidget': self.searchwidget,
        'filters': filters,
        'geojson': request.link(self, name='+geojson'),
        'submit': request.link(self, name='+submit'),
        'show_thumbnails': thumbnail and True or False,
        'thumbnail_link': thumbnail_link
    }


@OrgApp.json(
    model=DirectoryEntryCollection,
    permission=Public,
    name='geojson')
def view_geojson(self, request):
    q = self.query()
    q = q.with_entities(
        DirectoryEntry.id,
        DirectoryEntry.name,
        DirectoryEntry.title,
        DirectoryEntry.lead,
        DirectoryEntry.content["coordinates"]["lat"].label('lat'),
        DirectoryEntry.content["coordinates"]["lon"].label('lon')
    )
    q = q.filter(DirectoryEntry.content["coordinates"]["lat"] != None)

    url_prefix = request.class_link(DirectoryEntry, {
        'directory_name': self.directory.name,
        'name': ''
    })

    return tuple({
        'type': "Feature",
        'properties': {
            'name': e.name,
            'title': e.title,
            'lead': e.lead,
            'link': url_prefix + e.name
        },
        'geometry': {
            'coordinates': [e.lon, e.lat],
            'type': "Point"
        }
    } for e in q)


@OrgApp.form(
    model=DirectoryEntryCollection,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='new')
def handle_new_directory_entry(self, request, form):
    if form.submitted(request):
        entry = self.directory.add_by_form(form, type='extended')

        request.success(_("Added a new directory entry"))
        return request.redirect(request.link(entry))

    if form.errors:
        for field in form.match_fields(include_classes=(UploadField, )):
            getattr(form, field).data = {}

    layout = DirectoryEntryCollectionLayout(self, request)
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(_("New"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': _("New Directory Entry"),
        'form': form,
    }


@OrgApp.form(
    model=DirectoryEntry,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='edit')
def handle_edit_directory_entry(self, request, form):
    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    layout = DirectoryEntryLayout(self, request)
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
    }


@OrgApp.form(model=DirectoryEntryCollection,
             permission=Public,
             template='directory_entry_submission_form.pt',
             form=get_submission_form_class,
             name='submit')
def handle_submit_directory_entry(self, request, form):

    if not self.directory.enable_submissions:
        raise HTTPForbidden()

    title = _("Submit a New Directory Entry")

    if form.submitted(request):
        forms = FormCollection(request.session)

        # required by the form submissions collection
        form._source = self.directory.structure

        # the price per submission
        if self.directory.price == 'paid':
            amount = self.directory.price_per_submission
        else:
            amount = 0.0

        submission = forms.submissions.add_external(
            form=form,
            state='pending',
            payment_method=self.directory.payment_method,
            email=form.submitter.data,
            meta={
                'handler_code': 'DIR',
                'directory': self.directory.id.hex,
                'price': {
                    'amount': amount,
                    'currency': self.directory.currency
                },
                'extensions': tuple(
                    ext for ext in self.directory.extensions
                    if ext != 'submitter'
                )
            }
        )

        # remove old submission while we are at it
        self.directory.remove_old_pending_submissions()

        url = URL(request.link(submission))
        url = url.query_param('title', request.translate(title))

        return request.redirect(url.as_string())

    layout = DirectoryEntryCollectionLayout(self, request)
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(title, '#'))
    layout.editbar_links = []

    return {
        'directory': self.directory,
        'form': form,
        'layout': layout,
        'title': title,
    }


@OrgApp.html(
    model=DirectoryEntry,
    permission=Public,
    template='directory_entry.pt')
def view_directory_entry(self, request):

    return {
        'layout': DirectoryEntryLayout(self, request),
        'title': self.title,
        'entry': self
    }


@OrgApp.view(
    model=DirectoryEntry,
    permission=Private,
    request_method='DELETE')
def delete_directory_entry(self, request):
    request.assert_valid_csrf_token()

    session = request.session
    session.delete(self)

    request.success(_("The entry was deleted"))


@OrgApp.form(model=DirectoryEntryCollection, permission=Private, name='export',
             template='export.pt', form=ExportForm)
def view_export(self, request, form):

    layout = DirectoryEntryCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        url = URL(request.link(self, '+zip'))
        url = url.query_param('format', form.format)

        return request.redirect(url.as_string())

    return {
        'layout': layout,
        'title': _("Export"),
        'form': form,
        'explanation': _(
            "Exports all entries of this directory. The resulting zipfile "
            "contains the selected format as well as metadata and "
            "images/files if the directory contains any."
        )
    }


@OrgApp.view(model=DirectoryEntryCollection, permission=Private, name='zip')
def view_zip_file(self, request):
    layout = DirectoryEntryCollectionLayout(self, request)

    format = request.params.get('format', 'json')
    formatter = layout.export_formatter(format)

    def transform(key, value):
        return formatter(key), formatter(value)

    with NamedTemporaryFile() as f:
        archive = DirectoryZipArchive(f.name + '.zip', format, transform)
        archive.write(self.directory)

        response = render_file(str(archive.path), request)

    filename = ' '.join((
        self.directory.name, layout.format_date(layout.now(), 'datetime')))
    filename = re.sub(r'[\.:]+', '-', filename)

    response.headers['Content-Disposition']\
        = 'attachment; filename="{}"'.format(filename)

    return response


@OrgApp.form(model=DirectoryEntryCollection, permission=Private, name='import',
             template='directory_import.pt', form=DirectoryImportForm)
def view_import(self, request, form):
    error = None

    layout = DirectoryEntryCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Import"), '#'))
    layout.editbar_links = None

    if form.submitted(request):
        try:
            imported = form.run_import(target=self.directory)
        except MissingColumnError as e:
            request.alert(_("The column ${name} is missing", mapping={
                'name': self.directory.field_by_id(e.column).human_id
            }))
        except MissingFileError as e:
            request.alert(_("The file ${name} is missing", mapping={
                'name': e.name
            }))
        except DuplicateEntryError as e:
            request.alert(_("The entry ${name} exists twice", mapping={
                'name': e.name
            }))
        except ValidationError as e:
            error = e
        except NotImplementedError as e:
            request.alert(_(
                "The given file is invalid, does it include a metadata.json "
                "with a data.xlsx, data.csv, or data.json?"
            ))
        else:
            notify = imported and request.success or request.warning
            notify(_("Imported ${count} entries", mapping={
                'count': imported
            }))

            return request.redirect(request.link(self))

        # no success if we land here
        transaction.abort()

    return {
        'layout': layout,
        'title': _("Import"),
        'form': form,
        'explanation': _(
            "Updates the directory configuration and imports all entries "
            "given in the ZIP file. The format is the same as produced by "
            "the export function. Note that only 100 items are imported at a "
            "time. To import more items repeat the import accordingly."
        ),
        'directory': self.directory,
        'error': error,
        'error_translate': lambda text: request.translate(_(text)),
    }


@OrgApp.view(
    model=DirectorySubmissionAction,
    permission=Private,
    request_method='POST'
)
def execute_submission_action(self, request):
    return self.execute(request)
