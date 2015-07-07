""" Contains the paths to the different models served by onegov.town. """

from onegov.town.app import TownApp
from onegov.town.models import (
    Editor,
    File,
    FileCollection,
    Image,
    ImageCollection,
    News,
    Thumbnail,
    Topic,
    Town
)
from onegov.form import (
    FormDefinition,
    FormCollection,
    FormSubmissionFile,
    FormSubmissionCollection,
    CompleteFormSubmission,
    PendingFormSubmission
)
from onegov.page import PageCollection
from onegov.people import Person, PersonCollection


@TownApp.path(model=Town, path='/')
def get_town(app):
    return app.town


@TownApp.path(model=Topic, path='/themen', absorb=True)
def get_topic(app, absorb):
    return PageCollection(app.session()).by_path(absorb, ensure_type='topic')


@TownApp.path(model=News, path='/aktuelles', absorb=True)
def get_news(app, absorb):
    absorb = '/{}/{}'.format('aktuelles', absorb)
    return PageCollection(app.session()).by_path(absorb, ensure_type='news')


@TownApp.path(model=FileCollection, path='/dateien')
def get_files(app):
    return FileCollection(app)


@TownApp.path(model=File, path='/datei/{filename}')
def get_file(app, filename):
    return FileCollection(app).get_file_by_filename(filename)


@TownApp.path(model=ImageCollection, path='/bilder')
def get_images(app):
    return ImageCollection(app)


@TownApp.path(model=Image, path='/bild/{filename}')
def get_image(app, filename):
    return ImageCollection(app).get_file_by_filename(filename)


@TownApp.path(model=Thumbnail, path='/thumbnails/{filename}')
def get_thumbnail(app, filename):
    return ImageCollection(app).get_thumbnail_by_filename(filename)


@TownApp.path(model=FormCollection, path='/formulare')
def get_forms(app):
    return FormCollection(app.session())


@TownApp.path(model=FormDefinition, path='/formular/{name}')
def get_form(app, name):
    return FormCollection(app.session()).definitions.by_name(name)


@TownApp.path(model=FormSubmissionCollection, path='/formular/{name}/eingaben')
def get_form_submissions(app, name):
    return FormCollection(app.session()).scoped_submissions(name)


@TownApp.path(model=PendingFormSubmission, path='/formular-eingabe/{id}')
def get_pending_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='pending', current_only=True)


@TownApp.path(model=CompleteFormSubmission, path='/formular-eingang/{id}')
def get_complete_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='complete', current_only=False)


@TownApp.path(model=FormSubmissionFile, path='/formular-datei/{id}')
def get_form_submission_file(app, id):
    return FormCollection(app.session()).submissions.file_by_id(id)


@TownApp.path(model=Editor, path='/editor/{action}/{trait}/{page_id}')
def get_editor(app, action, trait, page_id):
    if not Editor.is_supported_action(action):
        return None

    page = PageCollection(app.session()).by_id(page_id)

    if not page.is_supported_trait(trait):
        return None

    if page is not None:
        return Editor(action=action, page=page, trait=trait)


@TownApp.path(model=PersonCollection, path='/personen')
def get_people(app):
    return PersonCollection(app.session())


@TownApp.path(model=Person, path='/person/{id}')
def get_person(app, id):
    return PersonCollection(app.session()).by_id(id)
