""" Contains the paths to the different models served by onegov.town. """

from onegov.town.app import TownApp
from onegov.town.model import (
    Image,
    ImageCollection,
    Thumbnail,
    LinkEditor,
    PageEditor,
    Town
)
from onegov.page import Page, PageCollection


@TownApp.path(model=Town, path='/')
def get_town(app):
    return app.town


@TownApp.path(model=Page, path='/themen', absorb=True)
def get_page(app, absorb):
    return PageCollection(app.session()).by_path(absorb)


@TownApp.path(model=ImageCollection, path='/bilder')
def get_images(app):
    return ImageCollection(app)


@TownApp.path(model=Image, path='/bild/{filename}')
def get_image(app, filename):
    return ImageCollection(app).get_image_by_filename(filename)


@TownApp.path(model=Thumbnail, path='/thumbnails/{filename}')
def get_thumbnail(app, filename):
    return ImageCollection(app).get_thumbnail_by_filename(filename)


@TownApp.path(model=PageEditor, path='/editor/page/{page_id}/{action}')
def get_page_editor(app, page_id, action):
    page = PageCollection(app.session()).by_id(page_id)

    if page is None:
        return

    return PageEditor(action=action, page=page)


@TownApp.path(model=LinkEditor, path='/editor/link/{page_id}/{action}')
def get_link_editor(app, page_id, action):
    page = PageCollection(app.session()).by_id(page_id)

    if page is None:
        return

    return LinkEditor(action=action, page=page)
