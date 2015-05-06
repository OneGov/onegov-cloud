""" Contains the paths to the different models served by onegov.town. """

from onegov.town.app import TownApp
from onegov.town.models import (
    Image,
    ImageCollection,
    Thumbnail,
    Editor,
    Town,
    TypedPage
)
from onegov.page import Page, PageCollection


@TownApp.path(model=Town, path='/')
def get_town(app):
    return app.town


@TownApp.path(model=Page, path='/themen', absorb=True)
def get_page(app, absorb):
    return TypedPage.from_page(
        page=PageCollection(app.session()).by_path(absorb),
        acceptable_types=('page', 'link', 'town-root')
    )


@TownApp.path(model=ImageCollection, path='/bilder')
def get_images(app):
    return ImageCollection(app)


@TownApp.path(model=Image, path='/bild/{filename}')
def get_image(app, filename):
    return ImageCollection(app).get_image_by_filename(filename)


@TownApp.path(model=Thumbnail, path='/thumbnails/{filename}')
def get_thumbnail(app, filename):
    return ImageCollection(app).get_thumbnail_by_filename(filename)


@TownApp.path(model=Editor, path='/editor/{page_type}/{page_id}/{action}')
def get_editor(app, page_type, page_id, action):
    page = TypedPage.from_page(PageCollection(app.session()).by_id(page_id))

    if page is not None:
        return Editor(action=action, page=page, page_type=page_type)
