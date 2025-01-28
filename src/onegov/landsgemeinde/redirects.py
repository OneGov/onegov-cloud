from __future__ import annotations
from onegov.core.redirect import Redirect
from onegov.landsgemeinde import LandsgemeindeApp


@LandsgemeindeApp.path(path='/film', absorb=True)
class FilmRedirect(Redirect):
    to = '/topics/film'
