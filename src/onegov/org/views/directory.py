import re
import transaction

from collections import defaultdict
from onegov.core.security import Public, Private, Secret
from onegov.core.utils import render_file
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryEntry
from onegov.directory import DirectoryZipArchive
from onegov.directory.archive import DirectoryFileNotFound
from onegov.directory.errors import DuplicateEntryError
from onegov.directory.errors import MissingColumnError
from onegov.directory.errors import MissingFileError
from onegov.directory.errors import ValidationError
from onegov.form import FormCollection, as_internal_id
from onegov.form.errors import (
    InvalidFormSyntax, MixedTypeError, DuplicateLabelError)
from onegov.form.fields import UploadField
from onegov.org import OrgApp, _
from onegov.org.forms import DirectoryForm, DirectoryImportForm
from onegov.org.forms.generic import ExportForm
from onegov.org.layout import DirectoryCollectionLayout
from onegov.org.layout import DirectoryEntryCollectionLayout
from onegov.org.layout import DirectoryEntryLayout
from onegov.org.models import DirectorySubmissionAction
from onegov.org.models import ExtendedDirectory, ExtendedDirectoryEntry
from onegov.core.elements import Link
from purl import URL
from tempfile import NamedTemporaryFile
from webob.exc import HTTPForbidden
from wtforms import TextAreaField
from wtforms.validators import InputRequired

from onegov.org.models.directory import ExtendedDirectoryEntryCollection


from typing import cast, Any, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from onegov.core.types import JSON_ro, RenderData
    from onegov.directory.models.directory import DirectoryEntryForm
    from onegov.org.models.directory import ExtendedDirectoryEntryForm
    from onegov.org.request import OrgRequest
    from typing import type_check_only
    from webob import Response

    @type_check_only
    class DirectoryEntryWithNumber(ExtendedDirectoryEntry):
        number: str | int | None


def get_directory_form_class(
    model: object,
    request: 'OrgRequest'
) -> type[DirectoryForm]:
    return ExtendedDirectory().with_content_extensions(DirectoryForm, request)


def get_directory_entry_form_class(
    model: ExtendedDirectoryEntry,
    request: 'OrgRequest'
) -> type['DirectoryEntryForm']:

    form_class = ExtendedDirectoryEntry().with_content_extensions(
        model.directory.form_class, request)

    class InternalNotesAndOptionalMapPublicationForm(
        form_class  # type:ignore
    ):
        internal_notes = TextAreaField(
            label=_("Internal Notes"),
            fieldset=_("Administrative"),
            render_kw={'rows': 7}
        )

        def on_request(self) -> None:
            # just a little safety guard so we for sure don't skip
            # an on_request call that should have been called
            if hasattr(super(), 'on_request'):
                super().on_request()

            if not self.request.is_manager:
                self.delete_field('internal_notes')

            if model.directory.enable_map == 'no':
                self.delete_field('coordinates')

            if not model.directory.enable_publication and not request.is_admin:
                self.delete_field('publication_start')
                self.delete_field('publication_end')
            elif model.directory.required_publication:
                self.publication_start.validators[0] = InputRequired()
                self.publication_end.validators[0] = InputRequired()

    return InternalNotesAndOptionalMapPublicationForm


def get_submission_form_class(
    model: ExtendedDirectoryEntry,
    request: 'OrgRequest'
) -> type['ExtendedDirectoryEntryForm']:
    return model.directory.form_class_for_submissions(change_request=False)


def get_change_request_form_class(
    model: ExtendedDirectoryEntry,
    request: 'OrgRequest'
) -> type['ExtendedDirectoryEntryForm']:
    return model.directory.form_class_for_submissions(change_request=True)


@OrgApp.html(
    model=DirectoryCollection,
    template='directories.pt',
    permission=Public)
def view_directories(
    self: DirectoryCollection[Any],
    request: 'OrgRequest',
    layout: DirectoryCollectionLayout | None = None
) -> 'RenderData':

    return {
        'title': _("Directories"),
        'layout': layout or DirectoryCollectionLayout(self, request),
        'directories': request.exclude_invisible(self.query()),
        'link': lambda directory: request.link(
            ExtendedDirectoryEntryCollection(
                directory,
                published_only=not request.is_manager
            )
        )
    }


@OrgApp.view(model=Directory, permission=Public)
def view_directory_redirect(
    self: Directory,
    request: 'OrgRequest'
) -> 'Response':
    return request.redirect(request.class_link(
        ExtendedDirectoryEntryCollection, {'directory_name': self.name}
    ))


@OrgApp.form(model=DirectoryCollection, name='new', template='form.pt',
             permission=Secret, form=get_directory_form_class)
def handle_new_directory(
    self: DirectoryCollection[Any],
    request: 'OrgRequest',
    form: DirectoryForm,
    layout: DirectoryCollectionLayout | None = None
) -> 'RenderData | Response':

    if form.submitted(request):
        try:
            directory = self.add_by_form(form, properties=('configuration', ))
        except DuplicateEntryError as e:
            request.alert(_("The entry ${name} exists twice", mapping={
                'name': e.name
            }))
            transaction.abort()
            return request.redirect(request.link(self))

        request.success(_("Added a new directory"))
        return request.redirect(
            request.link(ExtendedDirectoryEntryCollection(directory)))

    layout = layout or DirectoryCollectionLayout(self, request)
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


@OrgApp.form(model=ExtendedDirectoryEntryCollection, name='edit',
             template='directory_form.pt', permission=Secret,
             form=get_directory_form_class)
def handle_edit_directory(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest',
    form: DirectoryForm,
    layout: DirectoryCollectionLayout | None = None
) -> 'RenderData | Response':

    migration = None
    error = None

    try:
        if form.submitted(request):
            save_changes = True

            if self.directory.entries:
                assert form.structure.data is not None
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
                            form.action += '&confirm=1'  # type:ignore
                            save_changes = False

            if save_changes:
                form.populate_obj(self.directory)

                try:
                    self.session.flush()
                except ValidationError as e:
                    error = e
                    error.link = request.class_link(  # type:ignore
                        DirectoryEntry,
                        {
                            'directory_name': self.directory.name,
                            'name': e.entry.name
                        }
                    )
                    transaction.abort()
                else:
                    request.success(_("Your changes were saved"))
                    return request.redirect(request.link(self))

        elif not request.POST:
            form.process(obj=self.directory)
    except InvalidFormSyntax as e:
        request.warning(
            _("Syntax Error in line ${line}", mapping={'line': e.line})
        )
    except AttributeError:
        request.warning(_("Syntax error in form"))

    except MixedTypeError as e:
        request.warning(
            _("Syntax error in field ${field_name}",
              mapping={'field_name': e.field_name})
        )
    except DuplicateLabelError as e:
        request.warning(
            _("Error: Duplicate label ${label}", mapping={'label': e.label})
        )

    layout = layout or DirectoryCollectionLayout(self, request)
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
    model=ExtendedDirectoryEntryCollection,
    permission=Secret,
    request_method='DELETE')
def delete_directory(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest'
) -> None:

    request.assert_valid_csrf_token()

    session = request.session

    for entry in self.directory.entries:
        session.delete(entry)

    DirectoryCollection(session).delete(self.directory)
    request.success(_("The directory was deleted"))


class Filter(NamedTuple):
    title: str
    tags: 'Sequence[Link]'


def get_filters(
    request: 'OrgRequest',
    self: ExtendedDirectoryEntryCollection,
    keyword_counts: 'Mapping[str, Mapping[str, int]] | None' = None,
    view_name: str = ''
) -> list[Filter]:

    filters = []
    empty = ()

    # FIXME: It seems kind of strange to make this dependent on the fields
    #        of the directory, shouldn't this depend on the type of the
    #        filter instead? Even if a directory can only have one value
    #        you should still be able to filter for two distinct types of
    #        entries. One could even argue that this should always be a
    #        multi-select, regardless of what the filter form declares.
    radio_fields = {
        f.id for f in self.directory.fields if f.type == 'radio'
    }

    def link_title(field_id: str, value: str) -> str:
        if keyword_counts is None:
            return value
        count = keyword_counts.get(field_id, {}).get(value, 0)
        return f'{value} ({count})'

    for keyword, title, values in self.available_filters(sort_choices=False):
        singular = keyword in radio_fields
        filters.append(Filter(title=title, tags=tuple(
            Link(
                text=link_title(keyword, value),
                active=value in self.keywords.get(keyword, empty),
                url=request.link(
                    self.for_toggled_keyword_value(
                        keyword,
                        value,
                        singular=singular
                    ),
                    name=view_name
                ),
                rounded=singular
            )
            for value in values
        )))

    return filters


def keyword_count(
    request: 'OrgRequest',
    collection: ExtendedDirectoryEntryCollection
) -> dict[str, dict[str, int]]:

    self = collection
    keywords = tuple(
        as_internal_id(k)
        for k in self.directory.configuration.keywords or ()
    )
    fields = {f.id: f for f in self.directory.fields if f.id in keywords}
    counts: dict[str, dict[str, int]] = {}
    for model in request.exclude_invisible(self.without_keywords().query()):
        for entry in model.keywords:
            field_id, value = entry.split(':', 1)
            if field_id in fields:
                f_count = counts.setdefault(field_id, defaultdict(int))
                f_count[value] += 1
    return counts


@OrgApp.html(
    model=ExtendedDirectoryEntryCollection,
    permission=Public,
    template='directory.pt')
def view_directory(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest',
    layout: DirectoryEntryCollectionLayout | None = None
) -> 'RenderData':

    entries = request.exclude_invisible(self.query())
    for i, e in enumerate(entries):
        e = cast('DirectoryEntryWithNumber', e)
        if self.directory.numbering == 'custom':
            assert isinstance(self.directory.numbers, str)
            e.number = e.content['values'].get(
                as_internal_id(self.directory.numbers)) or 'x'
        elif self.directory.numbering == 'standard':
            e.number = i + 1
        else:
            e.number = None
    keyword_counts = keyword_count(request, self)
    filters = get_filters(request, self, keyword_counts)
    layout = layout or DirectoryEntryCollectionLayout(self, request)

    return {
        'layout': layout,
        'title': self.directory.title,
        'entries': entries,
        'directory': self.directory,
        'search_widget': self.search_widget,
        'filters': filters,
        'geojson': request.link(self, name='+geojson'),
        'submit': request.link(self, name='+submit'),
        'show_thumbnails': layout.thumbnail_field_id and True or False,
        'thumbnail_link': layout.thumbnail_link,
        'overview_two_columns': self.directory.overview_two_columns
    }


@OrgApp.json(
    model=ExtendedDirectoryEntryCollection,
    permission=Public,
    name='geojson')
def view_geojson(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest'
) -> 'JSON_ro':

    q = self.query().with_entities(
        DirectoryEntry.id,
        DirectoryEntry.name,
        DirectoryEntry.title,
        DirectoryEntry.lead,
        DirectoryEntry.content["coordinates"]["lat"].label('lat'),
        DirectoryEntry.content["coordinates"]["lon"].label('lon'),
        DirectoryEntry.meta["access"].label('access'),
    )
    q = q.filter(DirectoryEntry.content["coordinates"]["lat"] != None)

    with_categories = request.params.get('with-categories', False)

    if with_categories:
        q = q.add_column(DirectoryEntry._keywords)

    # this could be done using a query, but that seems to be more verbose
    # FIXME: We should create a utility function that yields visibility
    #        based on role and access
    if request.is_manager:
        entries = q
    else:
        # guests are allowed to see public and mtan views
        accesses = {
            'public',
            'mtan'
        }
        if request.current_username:
            # but members can also see member views
            accesses.add('member')

        entries = (c for c in q if not c.access or c.access in accesses)

    url_prefix = request.class_link(DirectoryEntry, {
        'directory_name': self.directory.name,
        'name': ''
    })

    # FIXME: For better type safety we should define a NamedTuple that
    #        matches our query above
    def as_dict(entry: Any) -> dict[str, Any]:
        result: dict[str, Any] = {
            'type': "Feature",
            'properties': {
                'name': entry.name,
                'title': entry.title,
                'lead': entry.lead,
                'link': url_prefix + entry.name
            },
            'geometry': {
                'coordinates': (entry.lon, entry.lat),
                'type': "Point"
            }
        }

        if with_categories:
            categories = defaultdict(list)

            for item in entry._keywords.keys():
                k, v = item.split(':', 1)
                categories[k].append(v)

            result['properties']['categories'] = categories

        return result

    return tuple(as_dict(e) for e in entries)


@OrgApp.form(
    model=ExtendedDirectoryEntryCollection,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='new')
def handle_new_directory_entry(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest',
    form: 'DirectoryEntryForm',
    layout: DirectoryEntryCollectionLayout | None = None
) -> 'RenderData | Response':

    if form.submitted(request):
        try:
            entry = self.directory.add_by_form(form, type=(
                'extended'))
        except DuplicateEntryError as e:
            request.alert(_("The entry ${name} exists twice", mapping={
                'name': e.name
            }))
            transaction.abort()
            return request.redirect(request.link(self))

        request.success(_("Added a new directory entry"))
        return request.redirect(request.link(entry))

    if form.errors:
        for field in form.match_fields(include_classes=(UploadField, )):
            getattr(form, field).data = {}

    layout = layout or DirectoryEntryCollectionLayout(self, request)
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
def handle_edit_directory_entry(
    self: DirectoryEntry,
    request: 'OrgRequest',
    form: 'DirectoryEntryForm',
    layout: DirectoryEntryLayout | None = None
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    # FIXME: Should we only register this view for ExtendedDirectoryEntry?
    layout = layout or DirectoryEntryLayout(self, request)  # type:ignore
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
    }


@OrgApp.form(model=ExtendedDirectoryEntryCollection,
             permission=Public,
             template='directory_entry_submission_form.pt',
             form=get_submission_form_class,
             name='submit')
def handle_submit_directory_entry(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest',
    form: 'ExtendedDirectoryEntryForm',
    layout: DirectoryEntryCollectionLayout | None = None
) -> 'RenderData | Response':

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
            minimum_price_total=self.directory.minimum_price_total,
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
                ),
                **form.submitter_meta
            },
        )

        # remove old submission while we are at it
        self.directory.remove_old_pending_submissions()

        url = URL(request.link(submission))
        url = url.query_param('title', request.translate(title))

        return request.redirect(url.as_string())

    layout = layout or DirectoryEntryCollectionLayout(self, request)
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(title, '#'))
    layout.editbar_links = []

    return {
        'directory': self.directory,
        'form': form,
        'layout': layout,
        'title': title,
        'guideline': self.directory.submissions_guideline,
        'button_text': _('Continue')
    }


@OrgApp.form(model=ExtendedDirectoryEntry,
             permission=Public,
             template='directory_entry_submission_form.pt',
             form=get_change_request_form_class,
             name='change-request')
def handle_change_request(
    self: ExtendedDirectoryEntry,
    request: 'OrgRequest',
    form: 'ExtendedDirectoryEntryForm',
    layout: DirectoryEntryLayout | None = None
) -> 'RenderData | Response':

    title = _("Propose a change")

    if form.submitted(request):
        forms = FormCollection(request.session)

        # required by the form submissions collection
        form._source = self.directory.structure

        extensions = [
            ext for ext in self.directory.extensions if ext != 'submitter']
        extensions.append('change-request')

        submission = forms.submissions.add_external(
            form=form,
            state='pending',
            email=form.submitter.data,
            meta={
                'handler_code': 'DIR',
                'directory': self.directory.id.hex,
                'directory_entry': self.id.hex,
                'extensions': extensions,
                **form.submitter_meta
            }
        )

        # remove old submission while we are at it
        self.directory.remove_old_pending_submissions()

        url = URL(request.link(submission))
        url = url.query_param('title', request.translate(title))

        return request.redirect(url.as_string())

    elif not request.POST:
        form.process(obj=self)

    layout = layout or DirectoryEntryLayout(self, request)
    layout.include_code_editor()
    layout.breadcrumbs.append(Link(title, '#'))
    layout.editbar_links = []

    return {
        'directory': self.directory,
        'form': form,
        'layout': layout,
        'title': title,
        'hint': _(
            "To request a change, edit the fields you would like to change, "
            "leaving the other fields intact. Then submit your request."
        ),
        'guideline': self.directory.change_requests_guideline,
        'button_text': _('Continue')
    }


@OrgApp.html(
    model=ExtendedDirectoryEntry,
    permission=Public,
    template='directory_entry.pt')
def view_directory_entry(
    self: ExtendedDirectoryEntry,
    request: 'OrgRequest',
    layout: DirectoryEntryLayout | None = None
) -> 'RenderData':

    directory = self.directory

    siblings = request.exclude_invisible(ExtendedDirectoryEntryCollection(
        directory,
        published_only=not request.is_manager
    ).query())

    prev_entry: ExtendedDirectoryEntry | bool
    next_entry: ExtendedDirectoryEntry | bool
    more_entries: bool
    if self not in siblings:
        # we don't know where we're at within the collection so don't
        # show anything
        prev_entry = next_entry = more_entries = False
    else:
        entry_index = siblings.index(self)

        prev_entry = siblings[entry_index - 1] if entry_index != 0 else False
        next_entry = siblings[
            entry_index + 1] if entry_index != len(siblings) - 1 else False
        more_entries = bool(prev_entry or next_entry)

    return {
        'layout': layout or DirectoryEntryLayout(self, request),
        'title': self.title,
        'entry': self,
        'more_entries': more_entries,
        'prev_entry': prev_entry,
        'next_entry': next_entry
    }


@OrgApp.view(
    model=DirectoryEntry,
    permission=Private,
    request_method='DELETE')
def delete_directory_entry(
    self: DirectoryEntry,
    request: 'OrgRequest'
) -> None:

    request.assert_valid_csrf_token()

    session = request.session
    session.delete(self)

    request.success(_("The entry was deleted"))


@OrgApp.form(model=ExtendedDirectoryEntryCollection,
             permission=Public, name='export',
             template='export.pt', form=ExportForm)
def view_export(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest',
    form: ExportForm,
    layout: DirectoryEntryCollectionLayout | None = None
) -> 'RenderData | Response':

    if not request.is_visible(self.directory):
        return HTTPForbidden()

    layout = layout or DirectoryEntryCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export"), '#'))
    layout.editbar_links = None  # type:ignore[assignment]

    if form.submitted(request):
        url = URL(request.link(self, '+zip'))
        url = url.query_param('format', form.format)

        return request.redirect(url.as_string())

    filters = get_filters(request, self, keyword_count(request, self),
                          view_name='+export')

    if filters:
        pretext = _("On the right side, you can filter the entries of this "
                    "directory to export.")
    else:
        pretext = _("Exports all entries of this directory.")

    return {
        'layout': layout,
        'title': _("Export"),
        'form': form,
        'explanation': f'{request.translate(pretext)} ' + request.translate(_(
            "The resulting zipfile contains the selected format as well "
            "as metadata and images/files if the directory contains any."
        )),
        'filters': filters,
        'count': len(request.exclude_invisible(self.query().all()))
    }


@OrgApp.view(model=ExtendedDirectoryEntryCollection,
             permission=Public, name='zip')
def view_zip_file(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest'
) -> 'Response':

    if not request.is_visible(self.directory):
        return HTTPForbidden()

    layout = DirectoryEntryCollectionLayout(self, request)

    format = request.params.get('format')
    if not isinstance(format, str):
        format = 'json'
    formatter = layout.export_formatter(format)

    def transform(key: object, value: object) -> tuple[Any, Any]:
        return formatter(key), formatter(value)

    with NamedTemporaryFile() as f:
        archive = DirectoryZipArchive(f.name + '.zip', format, transform)
        try:
            archive.write(
                self.directory,
                entry_filter=request.exclude_invisible,
                query=self.query()
            )
        except DirectoryFileNotFound as err:
            entry = self.by_name(err.entry_name)
            entry_url = request.link(entry, name='edit')
            request.alert(
                _("You have been redirect to this entry because "
                  "it could not be exported due to missing file ${name}. "
                  "Please re-upload them and try again",
                  mapping={'name': err.filename})
            )
            return request.redirect(entry_url)

        response = render_file(str(archive.path), request)

    filename = ' '.join((
        self.directory.name, layout.format_date(layout.now(), 'datetime')))
    filename = re.sub(r'[\.:]+', '-', filename)
    filename = filename + '.zip'

    response.headers['Content-Disposition'] = (
        f'attachment; filename="{filename}"')

    return response


@OrgApp.form(model=ExtendedDirectoryEntryCollection,
             permission=Private, name='import',
             template='directory_import.pt', form=DirectoryImportForm)
def view_import(
    self: ExtendedDirectoryEntryCollection,
    request: 'OrgRequest',
    form: DirectoryImportForm,
    layout: DirectoryEntryCollectionLayout | None = None
) -> 'RenderData | Response':

    error = None

    layout = layout or DirectoryEntryCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Import"), '#'))
    layout.editbar_links = None  # type:ignore[assignment]

    if form.submitted(request):
        try:
            imported = form.run_import(target=self.directory)
        except MissingColumnError as e:
            field = self.directory.field_by_id(e.column)
            assert field is not None
            request.alert(_("The column ${name} is missing", mapping={
                'name': field.human_id
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
        except NotImplementedError:
            request.alert(_(
                "The given file is invalid, does it include a metadata.json "
                "with a data.xlsx, data.csv, or data.json?"
            ))
        else:
            notify = request.success if imported else request.warning
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
def execute_submission_action(
    self: DirectorySubmissionAction,
    request: 'OrgRequest'
) -> None:
    self.execute(request)
