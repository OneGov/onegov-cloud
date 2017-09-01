from onegov.core.security import Public, Private, Secret
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryEntry
from onegov.directory import DirectoryEntryCollection
from onegov.org import OrgApp, _
from onegov.org.forms import DirectoryForm
from onegov.org.layout import DirectoryCollectionLayout
from onegov.org.layout import DirectoryEntryCollectionLayout
from onegov.org.layout import DirectoryEntryLayout
from onegov.org.models import ExtendedDirectory, ExtendedDirectoryEntry
from onegov.org.new_elements import Link


def get_directory_form_class(model, request):
    return ExtendedDirectory().with_content_extensions(DirectoryForm, request)


def get_directory_entry_form_class(model, request):
    return ExtendedDirectoryEntry().with_content_extensions(
        model.directory.form_class, request)


@OrgApp.html(
    model=DirectoryCollection,
    template='directories.pt',
    permission=Public)
def view_directories(self, request):
    return {
        'title': _("Directories"),
        'layout': DirectoryCollectionLayout(self, request),
        'directories': tuple(self.query()),
        'link': lambda directory: request.link(
            DirectoryEntryCollection(directory)
        )
    }


@OrgApp.form(model=DirectoryCollection, name='neu', template='form.pt',
             permission=Secret, form=get_directory_form_class)
def handle_new_directory(self, request, form):
    if form.submitted(request):
        directory = self.add(
            title=form.title.data,
            lead=form.lead.data,
            structure=form.structure.data,
            configuration=DirectoryConfiguration.from_yaml(
                form.configuration.data
            )
        )

        request.success(_("Added a new directory"))
        return request.redirect(
            request.link(DirectoryEntryCollection(directory)))

    layout = DirectoryCollectionLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Directories"), request.link(self)),
        Link(_("New"), request.link(self, name='neu'))
    ]

    return {
        'layout': layout,
        'title': _("New Directory"),
        'form': form,
        'form_width': 'large',
    }


@OrgApp.form(model=DirectoryEntryCollection, template='form.pt',
             permission=Secret, form=get_directory_form_class,
             name='bearbeiten')
def handle_edit_directory(self, request, form):

    if form.submitted(request):
        form.populate_obj(self.directory)

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
    }


@OrgApp.view(
    model=DirectoryEntryCollection,
    permission=Secret,
    request_method='DELETE')
def delete_directory(self, request):
    request.assert_valid_csrf_token()

    DirectoryCollection(request.app.session()).delete(self.directory)
    request.success("The directory was deleted")


@OrgApp.html(
    model=DirectoryEntryCollection,
    permission=Public,
    template='directory.pt')
def view_directory(self, request):
    return {
        'layout': DirectoryEntryCollectionLayout(self, request),
        'title': self.directory.title,
        'entries': self.batch,
        'directory': self.directory
    }


@OrgApp.form(
    model=DirectoryEntryCollection,
    permission=Private,
    template='form.pt',
    form=get_directory_entry_form_class,
    name='neu')
def handle_new_directory_entry(self, request, form):
    if form.submitted(request):
        entry = self.directory.add(values=form.data, type='extended')
        form.populate_obj(entry)

        request.success(_("Added a new directory entry"))
        return request.redirect(request.link(entry))

    layout = DirectoryEntryCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("New"), '#'))

    return {
        'layout': layout,
        'title': _("New Directory Entry"),
        'form': form,
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
