from __future__ import annotations

from onegov.core.security import Public, Private, Secret
from onegov.directory import DirectoryCollection, Directory
from onegov.directory import DirectoryEntry
from onegov.org.forms.directory import DirectoryRecipientForm, DirectoryUrlForm
from onegov.org.views.directory import (
    view_directories, get_directory_form_class, handle_new_directory,
    handle_edit_directory, get_directory_entry_form_class, view_directory,
    handle_new_directory_entry, handle_edit_directory_entry, new_recipient,
    get_submission_form_class, handle_submit_directory_entry,
    get_change_request_form_class, handle_change_request,
    view_directory_entry, view_directory_entry_update_recipients,
    view_export, view_import, change_directory_url
)
from onegov.town6 import TownApp
from onegov.org.forms import DirectoryImportForm
from onegov.org.forms.generic import ExportForm
from onegov.org.models.directory import (
    ExtendedDirectoryEntry, ExtendedDirectoryEntryCollection)
from onegov.town6.layout import (
    DirectoryCollectionLayout,
    DirectoryEntryCollectionLayout,
    DirectoryEntryLayout)


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.directory.models.directory import DirectoryEntryForm
    from onegov.org.models.directory import ExtendedDirectoryEntryForm
    from onegov.org.forms import DirectoryForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=DirectoryCollection,
    template='directories.pt',
    permission=Public
)
def town_view_directories(
    self: DirectoryCollection[Any],
    request: TownRequest
) -> RenderData:
    return view_directories(
        self, request, DirectoryCollectionLayout(self, request))


@TownApp.form(
    model=DirectoryCollection,
    name='new',
    template='form.pt',
    permission=Secret,
    form=get_directory_form_class
)
def town_handle_new_directory(
    self: DirectoryCollection[Any],
    request: TownRequest,
    form: DirectoryForm
) -> RenderData | Response:
    return handle_new_directory(
        self, request, form, DirectoryCollectionLayout(self, request))


@TownApp.form(
    model=ExtendedDirectoryEntryCollection,
    name='edit',
    template='directory_form.pt',
    permission=Secret,
    form=get_directory_form_class
)
def town_handle_edit_directory(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest,
    form: DirectoryForm
) -> RenderData | Response:
    return handle_edit_directory(
        self, request, form, DirectoryCollectionLayout(self, request))


@TownApp.form(
    model=Directory,
    name='change-url',
    template='form.pt',
    permission=Private,
    form=DirectoryUrlForm
)
def town_change_directory_url(
    self: Directory,
    request: TownRequest,
    form: DirectoryUrlForm
) -> RenderData | Response:
    return change_directory_url(
        self, request, form,
        # FIXME: Should this be DefaultLayout? DirectoryCollection definitely
        #        seems wrong
        DirectoryCollectionLayout(self, request)  # type:ignore
    )


@TownApp.html(
    model=ExtendedDirectoryEntryCollection,
    permission=Public,
    template='directory.pt'
)
def town_view_directory(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest
) -> RenderData:
    return view_directory(
        self, request, DirectoryEntryCollectionLayout(self, request))


@TownApp.form(
    model=ExtendedDirectoryEntryCollection,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='new'
)
def town_handle_new_directory_entry(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest,
    form: DirectoryEntryForm
) -> RenderData | Response:
    return handle_new_directory_entry(
        self, request, form,
        DirectoryEntryCollectionLayout(self, request, hide_steps=True))


@TownApp.form(
    model=DirectoryEntry,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='edit'
)
def town_handle_edit_directory_entry(
    self: DirectoryEntry,
    request: TownRequest,
    form: DirectoryEntryForm
) -> RenderData | Response:
    return handle_edit_directory_entry(
        self, request, form,
        # FIXME: Should we only register this view for ExtendedDirectoryEntry?
        DirectoryEntryLayout(self, request))  # type:ignore[arg-type]


@TownApp.form(
    model=ExtendedDirectoryEntryCollection,
    permission=Public,
    template='directory_entry_submission_form.pt',
    form=get_submission_form_class,
    name='submit'
)
def town_handle_submit_directory_entry(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest,
    form: ExtendedDirectoryEntryForm
) -> RenderData | Response:
    return handle_submit_directory_entry(
        self, request, form, DirectoryEntryCollectionLayout(self, request))


@TownApp.form(
    model=ExtendedDirectoryEntry,
    permission=Public,
    template='directory_entry_submission_form.pt',
    form=get_change_request_form_class,
    name='change-request'
)
def town_handle_change_request(
    self: ExtendedDirectoryEntry,
    request: TownRequest,
    form: ExtendedDirectoryEntryForm
) -> RenderData | Response:
    return handle_change_request(
        self, request, form, DirectoryEntryLayout(self, request))


@TownApp.html(
    model=ExtendedDirectoryEntry,
    permission=Public,
    template='directory_entry.pt'
)
def town_view_directory_entry(
    self: ExtendedDirectoryEntry,
    request: TownRequest
) -> RenderData:
    return view_directory_entry(
        self, request, DirectoryEntryLayout(self, request))


@TownApp.form(
    model=ExtendedDirectoryEntryCollection,
    permission=Public,
    name='export',
    template='export.pt',
    form=ExportForm
)
def town_view_export(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest,
    form: ExportForm
) -> RenderData | Response:
    return view_export(
        self, request, form, DirectoryEntryCollectionLayout(self, request))


@TownApp.form(
    model=ExtendedDirectoryEntryCollection,
    permission=Private,
    name='import',
    template='directory_import.pt',
    form=DirectoryImportForm
)
def town_view_import(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest,
    form: DirectoryImportForm
) -> RenderData | Response:
    return view_import(
        self, request, form, DirectoryEntryCollectionLayout(self, request))


@TownApp.form(
    model=ExtendedDirectoryEntryCollection,
    name='new-recipient', template='form.pt',
    permission=Public, form=DirectoryRecipientForm
)
def town_new_recipient(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest,
    form: DirectoryRecipientForm
) -> RenderData | Response:

    layout = DirectoryEntryCollectionLayout(self, request)
    layout.hide_steps = True

    return new_recipient(self, request, form, layout)


@TownApp.html(
    model=ExtendedDirectoryEntryCollection,
    name='recipients', template='directory_entry_recipients.pt',
    permission=Private
)
def town_view_recipients(
    self: ExtendedDirectoryEntryCollection,
    request: TownRequest,
) -> RenderData | Response:

    layout = DirectoryEntryCollectionLayout(self, request)
    layout.hide_steps = True

    return view_directory_entry_update_recipients(self, request, layout)
