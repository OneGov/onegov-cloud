from onegov.org import OrgApp
from onegov.core.redirect import Redirect


@OrgApp.path(path='/benutzerverwaltung')
class BenutzerverwaltungRedirect(Redirect):
    to = '/usermanagement'


@OrgApp.path(path='/themen', absorb=True)
class ThemenRedirect(Redirect):
    to = '/topics'


@OrgApp.path(path='/aktuelles', absorb=True)
class AktuellesRedirect(Redirect):
    to = '/news'


@OrgApp.path(path='/dateien')
class DateienRedirect(Redirect):
    to = '/files'


@OrgApp.path(path='/bilder')
class BilderRedirect(Redirect):
    to = '/images'


@OrgApp.path(path='/exporte')
class ExporteRedirect(Redirect):
    to = '/exports'


@OrgApp.path(path='/formulare')
class FormulareRedirect(Redirect):
    to = '/forms'


@OrgApp.path(path='/formular', absorb=True)
class FormularRedirect(Redirect):
    to = '/form'


@OrgApp.path(path='/formular-eingabe', absorb=True)
class FormularEingabeRedirect(Redirect):
    to = '/form-preview'


@OrgApp.path(path='/formular-eingang', absorb=True)
class FormularEingangRedirect(Redirect):
    to = '/form-submission'


@OrgApp.path(path='/personen')
class PersonenRedirect(Redirect):
    to = '/people'


@OrgApp.path(path='/ressourcen')
class RessourcenRedirect(Redirect):
    to = '/resources'


@OrgApp.path(path='/ressource', absorb=True)
class RessourceRedirect(Redirect):
    to = '/resource'


@OrgApp.path(path='/einteilung', absorb=True)
class EinteilungRedirect(Redirect):
    to = '/allocation'


@OrgApp.path(path='/veranstaltungen')
class VeranstaltungenRedirect(Redirect):
    to = '/events'


@OrgApp.path(path='/veranstaltung', absorb=True)
class VeranstaltungRedirect(Redirect):
    to = '/event'


@OrgApp.path(path='/suche')
class SucheRedirect(Redirect):
    to = '/search'


@OrgApp.path(path='/abonnenten')
class AbonnentenRedirect(Redirect):
    to = '/subscribers'


@OrgApp.path(path='/datei', absorb=True)
class DateiRedirect(Redirect):
    to = '/file'


@OrgApp.path(path='/bild', absorb=True)
class BildRedirect(Redirect):
    to = '/image'


@OrgApp.path(path='/fotoalben')
class FotoalbenRedirect(Redirect):
    to = '/photoalbums'


@OrgApp.path(path='/fotoalbum', absorb=True)
class FotoalbumRedirect(Redirect):
    to = '/photoalbum'


@OrgApp.path(path='/ressourcen-empfang')
class RessourcenEmpfangRedirect(Redirect):
    to = '/resource-recipients'


@OrgApp.path(path='/ressourcen-empfaenger', absorb=True)
class RessourcenEmpfaengerRedirect(Redirect):
    to = '/resource-recipient'


@OrgApp.path(path='/zahlungsanbieter')
class ZahlungsanbieterRedirect(Redirect):
    to = '/payment-provider'


@OrgApp.path(path='/zahlungsanbieter-eintrag', absorb=True)
class ZahlungsanbieterEintragRedirect(Redirect):
    to = '/payment-provider-entry'


@OrgApp.path(path='/zahlung', absorb=True)
class ZahlungRedirect(Redirect):
    to = '/payment'


@OrgApp.path(path='/zahlungen')
class ZahlungenRedirect(Redirect):
    to = '/payments'
