import morepath

from onegov.core.security import Public, Private
from onegov.file import File
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.forms import ImageSetForm
from onegov.town.layout import ImageSetLayout, ImageSetCollectionLayout
from onegov.town.models import (
    ImageFile,
    ImageSet,
    ImageSetCollection,
    ImageFileCollection
)
from purl import URL
from unidecode import unidecode


def get_form_class(self, request):
    if isinstance(self, ImageSetCollection):
        model = ImageSet()
    else:
        model = self

    return model.with_content_extensions(ImageSetForm, request)


@TownApp.html(model=ImageSetCollection, template='imagesets.pt',
              permission=Public)
def view_imagesets(self, request):

    # XXX add collation support to the core (create collations automatically)
    imagesets = self.query().all()
    imagesets = sorted(imagesets, key=lambda d: unidecode(d.title))

    return {
        'layout': ImageSetCollectionLayout(self, request),
        'title': _("Photo Albums"),
        'imagesets': request.exclude_invisible(imagesets)
    }


@TownApp.html(model=ImageSet, name='auswahl', template='select_images.pt',
              permission=Private, request_method='GET')
def select_images(self, request):

    collection = ImageFileCollection(request.app.session())
    selected = {f.id for f in self.files}

    def produce_image(id):
        return {
            'id': id,
            'src': request.class_link(File, {'id': id}, 'thumbnail'),
            'selected': id in selected
        }

    images = [
        {
            'group': request.translate(group),
            'images': tuple(produce_image(id) for group, id in items)
        } for group, items in collection.grouped_by_date()
    ]

    layout = ImageSetLayout(self, request)
    layout.breadcrumbs.append(Link(_("Select"), '#'))

    action = URL(request.link(self, 'auswahl')).query_param(
        'csrf-token', request.new_csrf_token())

    return {
        'layout': layout,
        'title': _("Select images"),
        'images': images,
        'action': action
    }


@TownApp.html(model=ImageSet, name='auswahl', template='select_images.pt',
              permission=Private, request_method='POST')
def handle_select_images(self, request):

    # we do custom form handling here, so we need to check for CSRF manually
    request.assert_valid_csrf_token()

    if not request.POST:
        self.files = []
    else:
        self.files = request.app.session().query(ImageFile)\
            .filter(ImageFile.id.in_(request.POST)).all()

    request.success(_("Your changes were saved"))

    return morepath.redirect(request.link(self))


@TownApp.form(model=ImageSetCollection, name='neu', template='form.pt',
              permission=Public, form=get_form_class)
def handle_new_imageset(self, request, form):

    if form.submitted(request):
        imageset = self.add(title=form.title.data)
        form.populate_obj(imageset)
        request.success(_("Added a new photo album"))

        return morepath.redirect(request.link(imageset))

    layout = ImageSetCollectionLayout(self, request)
    layout.include_editor()
    layout.breadcrumbs.append(Link(_("New"), '#'))

    return {
        'layout': layout,
        'title': _("New Photo Album"),
        'form': form,
    }


@TownApp.form(model=ImageSet, name='bearbeiten', template='form.pt',
              permission=Private, form=get_form_class)
def handle_edit_imageset(self, request, form):
    if form.submitted(request):
        form.populate_obj(self)

        request.success(_("Your changes were saved"))
        return morepath.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    layout = ImageSetLayout(self, request)
    layout.include_editor()
    layout.breadcrumbs.append(Link(_("Edit"), '#'))

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@TownApp.view(model=ImageSet, request_method='DELETE', permission=Private)
def handle_delete_imageset(self, request):
    request.assert_valid_csrf_token()

    collection = ImageSetCollection(request.app.session())
    collection.delete(self)


@TownApp.html(model=ImageSet, template='imageset.pt', permission=Public)
def view_imageset(self, request):

    return {
        'layout': ImageSetLayout(self, request),
        'title': self.title,
        'imageset': self
    }
