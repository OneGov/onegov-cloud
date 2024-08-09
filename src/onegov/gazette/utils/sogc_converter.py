from dateutil.parser import parse
from markupsafe import Markup
from onegov.gazette.models import Issue


from typing import overload
from typing import Any
from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from lxml.etree import _Element
    from sqlalchemy.orm import Session
    from typing import TypeVar

    _T = TypeVar('_T')


def html_converter(text: str) -> Markup:
    return Markup('<br>').join(line.strip() for line in text.split('\n'))


def line_converter(text: str) -> str:
    assert '\n' not in text, "Encountered line break in single line field"
    return text.strip()


class SogcConverter:

    """ The base class for all converters. """

    def __init__(self, root: '_Element') -> None:
        self.root = root

    # FIXME: This returning Literal[""] regardless of the conversion
    #        seems a little bit esoteric, we should probably return
    #        None unless we force the result to be a string
    @overload
    def get(
        self,
        path: str,
        converter: 'Callable[[str], Markup] | None' = html_converter,
        root: '_Element | None' = None
    ) -> Markup | Literal['']: ...

    @overload
    def get(
        self,
        path: str,
        converter: 'Callable[[str], _T]',
        root: '_Element | None' = None
    ) -> '_T | Literal[""]': ...

    def get(
        self,
        path: str,
        converter: 'Callable[[str], Any] | None' = html_converter,
        root: '_Element | None' = None
    ) -> Any:

        root = root if root is not None else self.root
        node = root.find(path)
        result = node.text.strip() if node is not None and node.text else ''
        if converter and result != '':
            result = converter(result)
        return result

    def get_line(self, path: str, root: '_Element | None' = None) -> str:
        return self.get(path, converter=line_converter, root=root)

    @property
    def title(self) -> str:
        return self.get_line('meta/title/de')

    @property
    def source(self) -> str:
        return self.get_line('meta/publicationNumber')

    @property
    def publication_date(self) -> 'datetime | Literal[""]':
        return self.get('meta/publicationDate', converter=parse)

    @property
    def expiration_date(self) -> 'datetime | Literal[""]':
        return self.get('meta/expirationDate', converter=parse)

    def issues(self, session: 'Session') -> list[str]:
        query = session.query(Issue.name)
        query = query.filter(Issue.date >= self.publication_date)
        query = query.order_by(Issue.date)
        row = query.first()
        return list(row) if row else []

    def p(
        self,
        value: object,
        title: str = '',
        title_break: bool = True,
        subtitle: str = '',
        subtitle_break: bool = False,
        fmt: str | None = None
    ) -> Markup:
        """ Adds a paragraph.

        Example::

            <p>
                <strong>title</strong><br>
                subtitle:<br>
                value
            </p>
        """
        if not value:
            return Markup("")

        if fmt == 'date':
            value = f"{value:%d.%m.%Y}"
        elif fmt == 'days':
            value = f"{value} Tage"
        elif fmt == 'currency':
            value = f"{value:.02f} CHF"

        if subtitle:
            if subtitle_break:
                template = Markup("{}:<br>{}")
            else:
                template = Markup("{}: {}")

            value = template.format(subtitle, value)

        if title:
            if title_break:
                template = Markup("<strong>{}</strong><br>{}")
            else:
                template = Markup("<strong>{}</strong>{}")

            value = template.format(title, value)

        return Markup("<p>{}</p>").format(value)


class KK(SogcConverter):

    @property
    def addition(self) -> Markup:
        value = self.get('content/addition')
        if value == 'legacy':
            return self.p("Erbschaft", "Zusatz")
        elif value == 'refusedLegacy':
            return self.p("ausgeschlagene Erbschaft", "Zusatz")
        elif value == 'custom':
            value = self.get('content/additionCustom')
            return self.p(value, "Zusatz")
        else:
            return Markup('')

    @property
    def comment_entry_deadline(self) -> Markup:
        return self.p(
            self.get('content/commentEntryDeadline'),
            "Kommentar zur Frist"
        )

    @property
    def days_after_publication(self) -> Markup:
        return self.p(
            self.get('content/daysAfterPublication', int),
            "Frist",
            fmt='days'
        )

    @property
    def debtor(self) -> Markup:
        debtor_type = self.get('content/debtor/selectType')
        if debtor_type == 'company':
            companies = self.root.findall('content/debtor/companies/company')
            result = Markup("")
            for company in companies:
                result += self.p(
                    self.get('name', root=company),
                    "Schuldner"
                )
                result += self.p(self.get('uid', root=company), subtitle="UID")
                result += self.p(
                    Markup('<br>').join((
                        Markup('{} {}').format(
                            self.get('address/street', root=company),
                            self.get('address/houseNumber', root=company)
                        ).strip(),
                        Markup('{} {}').format(
                            self.get('address/swissZipCode', root=company),
                            self.get('address/town', root=company)
                        ).strip()
                    )),
                )
                result += self.p(self.get('customAddress', root=company))
                result += self.p(self.get('country/name/de', root=company))
            return result

        elif debtor_type == 'person':
            result = self.p(
                Markup('{} {}').format(
                    self.get('content/debtor/person/prename'),
                    self.get('content/debtor/person/name')
                ).strip(),
                "Schuldner"
            )
            result += self.p(
                self.get('content/debtor/person/countryOfOrigin/name/de'),
                subtitle="Staatsbürger"
            )
            result += self.p(
                self.get('content/debtor/person/placeOfOrigin'),
                subtitle="Heimatort"
            )
            result += self.p(
                self.get('content/debtor/person/dateOfBirth', parse),
                subtitle="Geburtsdatum",
                fmt='date'
            )
            result += self.p(
                self.get('content/debtor/person/dateOfDeath', parse),
                subtitle="Todesdatum",
                fmt='date'
            )

            residence_type = self.get(
                'content/debtor/person/residence/selectType'
            )
            if residence_type == 'switzerland':
                path = 'content/debtor/person/addressSwitzerland'
                result += self.p(
                    Markup('<br>').join((
                        Markup('{} {}').format(
                            self.get(f'{path}/street'),
                            self.get(f'{path}/houseNumber')
                        ).strip(),
                        Markup('{} {}').format(
                            self.get(f'{path}/swissZipCode'),
                            self.get(f'{path}/town')
                        ).strip()
                    )),
                    subtitle="Wohnsitz",
                    subtitle_break=True
                )
            elif residence_type == 'foreign':
                path = 'content/debtor/person/addressForeign'
                result += self.p(
                    Markup('<br>').join((
                        self.get(f'{path}/addressCustomText'),
                        self.get(f'{path}/country/name/de')
                    )),
                    subtitle="Wohnsitz",
                    subtitle_break=True
                )
            elif residence_type == 'unknown':
                result += self.p("unbekannt", "Wohnsitz")

            result += self.p(
                self.get('content/debtor/person/personInformation'),
                subtitle="Weitere Informationen zur Person",
                subtitle_break=True
            )
            return result

        return Markup("")

    @property
    def entry_deadline(self) -> Markup:
        result = self.p(
            self.get('content/entryDeadline', parse),
            "Ablauf der Frist",
            fmt='date'
        )
        result += self.p(
            self.get('content/commentEntryDeadline'),
            "Kommentar zur Frist"
        )
        return result

    @property
    def information_about_edition(self) -> Markup:
        return self.p(
            self.get('content/informationAboutEdition'),
            "Angaben zur Auflage"
        )

    @property
    def legal(self) -> Markup:
        result = self.p(
            self.get('meta/legalRemedy'),
            "Rechtliche Hinweise und Fristen"
        )
        if self.get('content/or731b') == 'Yes':
            result += self.p("Aufgelöste Gesellschaft gemäss Art. 731b OR")
        result += self.p(
            self.get('content/additionalLegalRemedy'),
            "Ergänzende rechtliche Hinweise"
        )
        result += self.p(
            self.get('content/additionalLegalRemedyStatic'),
            "Ergänzende rechtliche Hinweise"
        )
        return result

    @property
    def remarks(self) -> Markup:
        return self.p(
            self.get('content/remarks'),
            "Bemerkungen"
        )

    @property
    def registration_office(self) -> Markup:
        return self.p(
            self.get('content/registrationOffice'),
            "Anmeldestelle"
        )

    @property
    def resolution_date(self) -> Markup:
        return self.p(
            self.get('content/resolutionDate', parse),
            "Datum der Konkurseröffnung",
            fmt='date'
        )


class KK01(KK):

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.resolution_date,
            self.addition,
            self.legal,
            self.remarks,
        ))


class KK02(KK):

    @property
    def proceeding(self) -> Markup:
        value = self.get('content/proceeding/selectType')
        if value == 'summary':
            return self.p("summarisch", "Art des Konkursverfahrens")
        elif value == 'ordinary':
            return self.p("ordentlich", "Art des Konkursverfahrens")
        elif value == 'other':
            value = self.get('content/otherProceeding')
            return self.p(value, "Art des Konkursverfahrens")
        else:
            return Markup('')

    @property
    def creditor_meeting(self) -> Markup:
        value_date = self.get('content/creditorMeeting/dateFrom', parse)
        value_time = self.get('content/creditorMeeting/time', parse)
        value_location = self.get('content/creditorMeeting/location')
        if not value_date:
            return Markup('')

        value = f"{value_date:%d.%m.%Y}"
        if value_time:
            value = f"{value_date:%d.%m.%Y} um {value_time:%H:%M}"
        if value_location:
            value = Markup("{}<br>{}").format(value, value_location)

        return self.p(value, "Gläubigerversammlung")

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.proceeding,
            self.resolution_date,
            self.creditor_meeting,
            self.days_after_publication,
            self.entry_deadline,
            self.registration_office,
            self.addition,
            self.legal,
            self.remarks,
        ))


class KK03(KK):

    @property
    def cessation_date(self) -> Markup:
        return self.p(
            self.get('content/cessationDate', parse),
            "Datum der Einstellung",
            fmt='date'
        )

    @property
    def advance_amount(self) -> Markup:
        return self.p(
            self.get('content/advanceAmount', float),
            "Betrag des Kostenvorschusses",
            fmt='currency'
        )

    @property
    def text(self) -> str:
        return Markup("").join((
            self.debtor,
            self.resolution_date,
            self.cessation_date,
            self.advance_amount,
            self.days_after_publication,
            self.entry_deadline,
            self.registration_office,
            self.addition,
            self.legal,
            self.remarks,
        ))


class KK04(KK):

    @property
    def claim_of_creditors(self) -> Markup:
        result = self.p(
            self.get('content/claimOfCreditors/daysAfterPublication', int),
            "Auflagefrist Kollokationsplan nach Publikation",
            fmt='days'
        )
        result += self.p(
            self.get('content/claimOfCreditors/entryDeadline', parse),
            "Ablauf der Auflagefrist Kollokationsplan",
            fmt='date'
        )
        result += self.p(
            self.get('content/claimOfCreditors/commentEntryDeadline'),
            "Kommentar zur Auflagefrist Kollokationsplan"
        )
        return result

    @property
    def inventory(self) -> Markup:
        result = self.p(
            self.get('content/inventory/daysAfterPublication', int),
            "Auflagefrist Inventar nach Publikation",
            fmt='days'
        )
        result += self.p(
            self.get('content/inventory/entryDeadline', parse),
            "Ablauf der Auflagefrist Inventar",
            fmt='date'
        )
        result += self.p(
            self.get('content/inventory/commentEntryDeadline'),
            "Kommentar zur Auflagefrist Inventar"
        )
        return result

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.claim_of_creditors,
            self.inventory,
            self.registration_office,
            self.addition,
            self.legal,
            self.remarks,
        ))


class KK05(KK):

    @property
    def location_circulation_authority(self) -> Markup:
        return self.p(
            self.get('content/locationCirculationAuthority'),
            "Angaben zur Auflage"
        )

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.location_circulation_authority,
            self.days_after_publication,
            self.entry_deadline,
            self.registration_office,
            self.legal,
            self.remarks,
        ))


class KK06(KK):

    @property
    def proceeding_end_date(self) -> Markup:
        return self.p(
            self.get('content/proceedingEndDate', parse),
            "Datum des Schlusses",
            fmt='date'
        )

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.proceeding_end_date,
            self.addition,
            self.legal,
            self.remarks,
        ))


class KK07(KK):

    @property
    def proceeding_revocation_date(self) -> Markup:
        return self.p(
            self.get('content/proceedingRevocationDate', parse),
            "Datum des Widerrufs",
            fmt='date'
        )

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.proceeding_revocation_date,
            self.legal,
            self.remarks,
        ))


class KK08(KK):

    @property
    def auction(self) -> Markup:
        value_date = self.get('content/auction/date', parse)
        value_time = self.get('content/auction/time', parse)
        value_location = self.get('content/auction/location')
        if not value_date:
            return Markup("")

        value = f"{value_date:%d.%m.%Y}"
        if value_time:
            value = f"{value_date:%d.%m.%Y} um {value_time:%H:%M}"
        if value_location:
            value = Markup("{}<br>{}").format(value, value_location)

        return self.p(value, "Steigerung")

    @property
    def auction_objects(self) -> Markup:
        return self.p(
            self.get('content/auctionObjects'),
            "Steigerungsobjekte"
        )

    @property
    def entry_start(self) -> Markup:
        return self.p(
            self.get('content/entryStart', parse),
            "Beginn der Frist",
            fmt='date'
        )

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.auction,
            self.auction_objects,
            self.information_about_edition,
            self.entry_start,
            self.entry_deadline,
            self.registration_office,
            self.addition,
            self.legal,
            self.remarks,
        ))


class KK09(KK):

    @property
    def affected_land(self) -> Markup:
        return self.p(
            self.get('content/affectedLand'),
            "Betroffenes Grundstück"
        )

    @property
    def appeal(self) -> Markup:
        result = self.p(
            self.get('content/appeal/daysAfterPublication', int),
            "Klage- und Beschwerdefrist",
            fmt='days'
        )
        result += self.p(
            self.get('content/appeal/entryDeadline', parse),
            "Ablauf der Klage- und Beschwerdefrist",
            fmt='date'
        )
        result += self.p(
            self.get('content/appeal/commentEntryDeadline'),
            "Kommentar zur Klage- und Beschwerdefrist"
        )
        return result

    @property
    def location_circulation_authority(self) -> Markup:
        return self.p(
            self.get('content/locationCirculationAuthority'),
            "Weitere Angaben"
        )

    @property
    def registration_office(self) -> Markup:
        result = self.p(
            self.get('content/registrationOfficeComplain'),
            "Anmeldestelle für Klagen"
        )
        result += self.p(
            self.get('content/registrationOfficeAppeal'),
            "Anmeldestelle für Beschwerden"
        )
        return result

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.debtor,
            self.affected_land,
            self.location_circulation_authority,
            self.information_about_edition,
            self.days_after_publication,
            self.entry_deadline,
            self.appeal,
            self.registration_office,
            self.legal,
            self.remarks,
        ))


class KK10(KK):

    @property
    def title(self) -> str:
        return self.get_line('content/title') or self.get_line('meta/title/de')

    @property
    def publication(self) -> Markup:
        return self.p(self.get('content/publication'))

    @property
    def text(self) -> Markup:
        return Markup("").join((
            self.publication,
            self.legal,
            self.remarks,
        ))
