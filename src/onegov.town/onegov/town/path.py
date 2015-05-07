""" Contains the paths to the different models served by onegov.town. """

from onegov.town.app import TownApp
from onegov.town.const import NEWS_PREFIX
from onegov.town.models import (
    Editor,
    Image,
    ImageCollection,
    News,
    Thumbnail,
    Topic,
    Town
)
from onegov.page import PageCollection


@TownApp.path(model=Town, path='/')
def get_town(app):
    return app.town


@TownApp.path(model=Topic, path='/themen', absorb=True)
def get_topic(app, absorb):
    return PageCollection(app.session()).by_path(absorb, ensure_type='topic')


@TownApp.path(model=News, path='/aktuelles', absorb=True)
def get_news(app, absorb):
    absorb = '/{}/{}'.format(NEWS_PREFIX, absorb)
    return PageCollection(app.session()).by_path(absorb, ensure_type='news')


@TownApp.path(model=ImageCollection, path='/bilder')
def get_images(app):
    return ImageCollection(app)


@TownApp.path(model=Image, path='/bild/{filename}')
def get_image(app, filename):
    return ImageCollection(app).get_image_by_filename(filename)


@TownApp.path(model=Thumbnail, path='/thumbnails/{filename}')
def get_thumbnail(app, filename):
    return ImageCollection(app).get_thumbnail_by_filename(filename)


@TownApp.path(
    model=Editor, path='/editor/{action}/{trait}/{page_id}')
def get_editor(app, action, trait, page_id):
    if not Editor.is_supported_action(action):
        return None

    page = PageCollection(app.session()).by_id(page_id)

    if not page.is_supported_trait(trait):
        return None

    if page is not None:
        return Editor(action=action, page=page, trait=trait)
