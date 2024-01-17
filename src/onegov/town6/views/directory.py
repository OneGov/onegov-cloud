
from onegov.core.security import Public, Private, Secret
from onegov.directory import DirectoryCollection, Directory
from onegov.directory import DirectoryEntry
from onegov.org.forms.directory import DirectoryUrlForm
from onegov.org.views.directory import (
    view_directories, get_directory_form_class, handle_new_directory,
    handle_edit_directory, get_directory_entry_form_class, view_directory,
    handle_new_directory_entry, handle_edit_directory_entry,
    get_submission_form_class, handle_submit_directory_entry,
    get_change_request_form_class, handle_change_request, view_directory_entry,
    view_export, view_import, change_directory_url
)
from onegov.town6 import TownApp
from onegov.org.forms import DirectoryImportForm
from onegov.org.forms.generic import ExportForm

from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.town6.layout import (
    DirectoryCollectionLayout,
    DirectoryEntryCollectionLayout,
    DirectoryEntryLayout,
    DefaultLayout,
)


@TownApp.html(
    model=DirectoryCollection,
    template='directories.pt',
    permission=Public)
def town_view_directories(self, request):
    return view_directories(
        self, request, DirectoryCollectionLayout(self, request))


@TownApp.form(model=DirectoryCollection, name='new', template='form.pt',
              permission=Secret, form=get_directory_form_class)
def town_handle_new_directory(self, request, form):
    return handle_new_directory(
        self, request, form, DirectoryCollectionLayout(self, request))


@TownApp.form(model=ExtendedDirectoryEntryCollection, name='edit',
              template='directory_form.pt', permission=Secret,
              form=get_directory_form_class)
def town_handle_edit_directory(self, request, form):
    return handle_edit_directory(
        self, request, form, DirectoryCollectionLayout(self, request))


@TownApp.form(
    model=Directory,
    name='change-url',
    template='form.pt',
    permission=Private,
    form=DirectoryUrlForm
)
def town_change_directory_url(self, request, form):
    return change_directory_url(
        self, request, form, DirectoryCollectionLayout(self, request)
    )


@TownApp.html(
    model=ExtendedDirectoryEntryCollection,
    permission=Public,
    template='directory.pt')
def town_view_directory(self, request):
    return view_directory(
        self, request, DirectoryEntryCollectionLayout(self, request))


@TownApp.form(
    model=ExtendedDirectoryEntryCollection,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='new')
def town_handle_new_directory_entry(self, request, form):
    return handle_new_directory_entry(
        self, request, form,
        DirectoryEntryCollectionLayout(self, request, hide_steps=True))


@TownApp.form(
    model=DirectoryEntry,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='edit')
def town_handle_edit_directory_entry(self, request, form):
    return handle_edit_directory_entry(
        self, request, form, DirectoryEntryLayout(self, request))


@TownApp.form(model=ExtendedDirectoryEntryCollection,
              permission=Public,
              template='directory_entry_submission_form.pt',
              form=get_submission_form_class,
              name='submit')
def town_handle_submit_directory_entry(self, request, form):
    return handle_submit_directory_entry(
        self, request, form, DirectoryEntryCollectionLayout(self, request))


@TownApp.form(model=DirectoryEntry,
              permission=Public,
              template='directory_entry_submission_form.pt',
              form=get_change_request_form_class,
              name='change-request')
def town_handle_change_request(self, request, form):
    return handle_change_request(
        self, request, form, DirectoryEntryLayout(self, request))


@TownApp.html(
    model=DirectoryEntry,
    permission=Public,
    template='directory_entry.pt')
def town_view_directory_entry(self, request):
    return view_directory_entry(
        self, request, DirectoryEntryLayout(self, request))


@TownApp.form(model=ExtendedDirectoryEntryCollection,
              permission=Public, name='export',
              template='export.pt', form=ExportForm)
def town_view_export(self, request, form):
    return view_export(
        self, request, form, DirectoryEntryCollectionLayout(self, request))


@TownApp.form(model=ExtendedDirectoryEntryCollection,
              permission=Private, name='import',
              template='directory_import.pt', form=DirectoryImportForm)
def town_view_import(self, request, form):
    return view_import(
        self, request, form, DirectoryEntryCollectionLayout(self, request))
