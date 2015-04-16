""" Contains the paths to the different models served by onegov.town. """

from onegov.town.app import TownApp
from onegov.town.model import ImageCollection, Town
from onegov.page import Page, PageCollection


@TownApp.path(model=Town, path='/')
def get_town(app):
    return app.town


@TownApp.path(model=Page, path='/gemeinde', absorb=True)
def get_page(app, absorb):
    return PageCollection(app.session()).by_path(absorb)


@TownApp.path(model=ImageCollection, path='/images')
def get_images(app):
    return ImageCollection(app)
