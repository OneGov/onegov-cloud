from collections import namedtuple
from onegov.core.security import Public, Private, Secret
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryEntry
from onegov.directory import DirectoryEntryCollection
from onegov.org import OrgApp, _
from onegov.org.forms import DirectoryForm
from onegov.org.layout import DirectoryCollectionLayout
from onegov.org.layout import DirectoryEntryCollectionLayout
from onegov.org.layout import DirectoryEntryLayout
from onegov.org.models import ExtendedDirectory, ExtendedDirectoryEntry
from onegov.org.new_elements import Link
from sqlalchemy import cast
from sqlalchemy import JSON


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


@OrgApp.form(model=DirectoryCollection, name='new', template='form.pt',
             permission=Secret, form=get_directory_form_class)
def handle_new_directory(self, request, form):
    if form.submitted(request):
        directory = self.add(
            title=form.title.data,
            lead=form.lead.data,
            structure=form.structure.data,
            configuration=form.configuration
        )

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
        'form_width': 'large',
    }


@OrgApp.form(model=DirectoryEntryCollection, name='edit',
             template='directory_entry_form.pt', permission=Secret,
             form=get_directory_form_class)
def handle_edit_directory(self, request, form):
    migration = None

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
    }


@OrgApp.view(
    model=DirectoryEntryCollection,
    permission=Secret,
    request_method='DELETE')
def delete_directory(self, request):
    request.assert_valid_csrf_token()

    session = request.app.session()

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

    for keyword, title, values in self.available_filters:
        filters.append(Filter(title=title, tags=tuple(
            Link(
                text=value,
                active=value in self.keywords.get(keyword, empty),
                url=request.link(self.for_filter(**{keyword: value}))
            ) for value in values
        )))

    return {
        'layout': DirectoryEntryCollectionLayout(self, request),
        'title': self.directory.title,
        'entries': self.batch,
        'directory': self.directory,
        'filters': filters,
        'geojson': request.link(self, name='+geojson')
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
        cast(DirectoryEntry.content, JSON)["coordinates"].label('coordinates')
    )

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
            'coordinates': [e.coordinates['lon'], e.coordinates['lat']],
            'type': "Point"
        }
    } for e in q if e.coordinates)


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

    layout = DirectoryEntryCollectionLayout(self, request)
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
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': self.title,
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


@OrgApp.view(
    model=DirectoryEntry,
    permission=Private,
    request_method='DELETE')
def delete_directory_entry(self, request):
    request.assert_valid_csrf_token()

    session = request.app.session()
    session.delete(self)

    request.success(_("The entry was deleted"))
