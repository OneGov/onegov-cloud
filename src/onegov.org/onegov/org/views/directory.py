from onegov.core.security import Public, Secret
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryEntryCollection
from onegov.org import OrgApp, _
from onegov.org.forms import DirectoryForm
from onegov.org.layout import DirectoryCollectionLayout
from onegov.org.new_elements import Link


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
             permission=Secret, form=DirectoryForm)
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
             permission=Secret, form=DirectoryForm, name='bearbeiten')
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
