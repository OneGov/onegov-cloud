from onegov.feriennet import FeriennetApp
from onegov.core.redirect import Redirect


@FeriennetApp.path(path='/angebote')
class AngeboteRedirect(Redirect):
    to = '/activities'


@FeriennetApp.path(path='/angebot', absorb=True)
class AngebotRedirect(Redirect):
    to = '/activity'


@FeriennetApp.path(path='/durchfuehrungen', absorb=True)
class DurchfuehrungenRedirect(Redirect):
    to = '/occasions'


@FeriennetApp.path(path='/perioden')
class PeriodenRedirect(Redirect):
    to = '/periods'


@FeriennetApp.path(path='/periode', absorb=True)
class PeriodeRedirect(Redirect):
    to = '/period'


@FeriennetApp.path(path='/meine-buchungen')
class MeineBuchungenRedirect(Redirect):
    to = '/my-bookings'


@FeriennetApp.path(path='/buchung', absorb=True)
class BuchungRedirect(Redirect):
    to = '/booking'


@FeriennetApp.path(path='/zuteilungen')
class ZuteilungenRedirect(Redirect):
    to = '/matching'


@FeriennetApp.path(path='/rechnungen')
class RechnungenRedirect(Redirect):
    to = '/billing'


@FeriennetApp.path(path='/rechnungsaktion', absorb=True)
class RechnungsAktionRedirect(Redirect):
    to = '/invoice-action'


@FeriennetApp.path(path='/meine-rechnungen')
class MeineRechnungenRedirect(Redirect):
    to = '/my-bills'


@FeriennetApp.path(path='/teilnehmer')
class TeilnehmerRedirect(Redirect):
    to = '/attendees'


@FeriennetApp.path(path='/mitteilungen')
class MitteilungenRedirect(Redirect):
    to = '/notifications'


@FeriennetApp.path(path='/mitteilung', absorb=True)
class MitteilungRedirect(Redirect):
    to = '/notification'
