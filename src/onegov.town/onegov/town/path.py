""" Contains the paths to the different models served by onegov.town. """

from onegov.town.app import TownApp
from onegov.town.model import Town


@TownApp.path(model=Town, path='/')
def get_town(app):
    # there's only one town per schema
    return app.session().query(Town).first()
