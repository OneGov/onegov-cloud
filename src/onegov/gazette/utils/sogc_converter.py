from dateutil.parser import parse
from onegov.gazette.models import Issue
from textwrap import dedent


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


def html_converter(text: str) -> str:
    # FIXME: Markupsafe
    return '<br>'.join((line.strip() for line in text.split('\n')))


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
        converter: 'Callable[[str], str] | None' = html_converter,
        root: '_Element | None' = None
    ) -> str: ...

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

    def dedent(self, text: str) -> str:
        return dedent(text).strip().replace('\n', '')

    @property
    def title(self) -> str:
        return self.get('meta/title/de')

    @property
    def source(self) -> str:
        return self.get('meta/publicationNumber')

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

    # FIXME: Markupsafe
    def p(
        self,
        value: object,
        title: str = '',
        title_break: bool = True,
        subtitle: str = '',
        subtitle_break: bool = False,
        fmt: str | None = None
    ) -> str:
        """ Adds a paragraph.

            <p>
                <strong>title</strong><br>
                subtitle:<br>
                value
            </p>
        """
        if not value:
            return ""

        if fmt == 'date':
            value = f"{value:%d.%m.%Y}"
        elif fmt == 'days':
            value = f"{value} Tage"
        elif fmt == 'currency':
            value = f"{value:.02f} CHF"

        if subtitle:
            if subtitle_break:
                value = f"{subtitle}:<br>{value}"
            else:
                value = f"{subtitle}: {value}"

        if title:
            if title_break:
                value = f"<strong>{title}</strong><br>{value}"
            else:
                value = f"<strong>{title}</strong>{value}"

        return f"<p>{value}</p>"


class KK(SogcConverter):

    @property
    def addition(self) -> str:
        value = self.get('content/addition')
        if value == 'legacy':
            return self.p("Erbschaft", "Zusatz")
        elif value == 'refusedLegacy':
            return self.p("ausgeschlagene Erbschaft", "Zusatz")
        elif value == 'custom':
            value = self.get('content/additionCustom')
            return self.p(value, "Zusatz")
        else:
            return ""

    @property
    def comment_entry_deadline(self) -> str:
        return self.p(
            self.get('content/commentEntryDeadline'),
            "Kommentar zur Frist"
        )

    @property
    def days_after_publication(self) -> str:
        return self.p(
            self.get('content/daysAfterPublication', int),
            "Frist",
            fmt='days'
        )

    @property
    def debtor(self) -> str | None:
        debtor_type = self.get('content/debtor/selectType')
        if debtor_type == 'company':
            companies = self.root.findall('content/debtor/companies/company')
            result = ""
            for company in companies:
                result += self.p(
                    self.get('name', root=company),
                    "Schuldner"
                )
                result += self.p(self.get('uid', root=company), subtitle="UID")
                result += self.p(
                    '<br>'.join([
                        '{} {}'.format(
                            self.get('address/street', root=company),
                            self.get('address/houseNumber', root=company)
                        ).strip(),
                        '{} {}'.format(
                            self.get('address/swissZipCode', root=company),
                            self.get('address/town', root=company)
                        ).strip()
                    ]),
                )
                result += self.p(self.get('customAddress', root=company))
                result += self.p(self.get('country/name/de', root=company))
            return result

        elif debtor_type == 'person':
            result = self.p(
                '{} {}'.format(
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
                    '<br>'.join([
                        '{} {}'.format(
                            self.get(f'{path}/street'),
                            self.get(f'{path}/houseNumber')
                        ).strip(),
                        '{} {}'.format(
                            self.get(f'{path}/swissZipCode'),
                            self.get(f'{path}/town')
                        ).strip()
                    ]),
                    subtitle="Wohnsitz",
                    subtitle_break=True
                )
            elif residence_type == 'foreign':
                path = 'content/debtor/person/addressForeign'
                result += self.p(
                    '<br>'.join([
                        self.get(f'{path}/addressCustomText'),
                        self.get(f'{path}/country/name/de')
                    ]),
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

        # FIXME: are we allowed to get here?
        return None

    @property
    def entry_deadline(self) -> str:
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
    def information_about_edition(self) -> str:
        return self.p(
            self.get('content/informationAboutEdition'),
            "Angaben zur Auflage"
        )

    @property
    def legal(self) -> str:
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
    def remarks(self) -> str:
        return self.p(
            self.get('content/remarks'),
            "Bemerkungen"
        )

    @property
    def registration_office(self) -> str:
        return self.p(
            self.get('content/registrationOffice'),
            "Anmeldestelle"
        )

    @property
    def resolution_date(self) -> str:
        return self.p(
            self.get('content/resolutionDate', parse),
            "Datum der Konkurseröffnung",
            fmt='date'
        )


class KK01(KK):

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.resolution_date}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK02(KK):

    @property
    def proceeding(self) -> str:
        value = self.get('content/proceeding/selectType')
        if value == 'summary':
            return self.p("summarisch", "Art des Konkursverfahrens")
        elif value == 'ordinary':
            return self.p("ordentlich", "Art des Konkursverfahrens")
        elif value == 'other':
            value = self.get('content/otherProceeding')
            return self.p(value, "Art des Konkursverfahrens")
        else:
            return ''

    @property
    def creditor_meeting(self) -> str:
        value_date = self.get('content/creditorMeeting/dateFrom', parse)
        value_time = self.get('content/creditorMeeting/time', parse)
        value_location = self.get('content/creditorMeeting/location')
        if not value_date:
            return ""

        value = f"{value_date:%d.%m.%Y}"
        if value_time:
            value = f"{value_date:%d.%m.%Y} um {value_time:%H:%M}"
        if value_location:
            value = f"{value}<br>{value_location}"

        return self.p(value, "Gläubigerversammlung")

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.proceeding}
        {self.resolution_date}
        {self.creditor_meeting}
        {self.days_after_publication}
        {self.entry_deadline}
        {self.registration_office}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK03(KK):

    @property
    def cessation_date(self) -> str:
        return self.p(
            self.get('content/cessationDate', parse),
            "Datum der Einstellung",
            fmt='date'
        )

    @property
    def advance_amount(self) -> str:
        return self.p(
            self.get('content/advanceAmount', float),
            "Betrag des Kostenvorschusses",
            fmt='currency'
        )

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.resolution_date}
        {self.cessation_date}
        {self.advance_amount}
        {self.days_after_publication}
        {self.entry_deadline}
        {self.registration_office}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK04(KK):

    @property
    def claim_of_creditors(self) -> str:
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
    def inventory(self) -> str:
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
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.claim_of_creditors}
        {self.inventory}
        {self.registration_office}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK05(KK):

    @property
    def location_circulation_authority(self) -> str:
        return self.p(
            self.get('content/locationCirculationAuthority'),
            "Angaben zur Auflage"
        )

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.location_circulation_authority}
        {self.days_after_publication}
        {self.entry_deadline}
        {self.registration_office}
        {self.legal}
        {self.remarks}
        """)


class KK06(KK):

    @property
    def proceeding_end_date(self) -> str:
        return self.p(
            self.get('content/proceedingEndDate', parse),
            "Datum des Schlusses",
            fmt='date'
        )

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.proceeding_end_date}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK07(KK):

    @property
    def proceeding_revocation_date(self) -> str:
        return self.p(
            self.get('content/proceedingRevocationDate', parse),
            "Datum des Widerrufs",
            fmt='date'
        )

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.proceeding_revocation_date}
        {self.legal}
        {self.remarks}
        """)


class KK08(KK):

    @property
    def auction(self) -> str:
        value_date = self.get('content/auction/date', parse)
        value_time = self.get('content/auction/time', parse)
        value_location = self.get('content/auction/location')
        if not value_date:
            return ""

        value = f"{value_date:%d.%m.%Y}"
        if value_time:
            value = f"{value_date:%d.%m.%Y} um {value_time:%H:%M}"
        if value_location:
            value = f"{value}<br>{value_location}"

        return self.p(value, "Steigerung")

    @property
    def auction_objects(self) -> str:
        return self.p(
            self.get('content/auctionObjects'),
            "Steigerungsobjekte"
        )

    @property
    def entry_start(self) -> str:
        return self.p(
            self.get('content/entryStart', parse),
            "Beginn der Frist",
            fmt='date'
        )

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.auction}
        {self.auction_objects}
        {self.information_about_edition}
        {self.entry_start}
        {self.entry_deadline}
        {self.registration_office}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK09(KK):

    @property
    def affected_land(self) -> str:
        return self.p(
            self.get('content/affectedLand'),
            "Betroffenes Grundstück"
        )

    @property
    def appeal(self) -> str:
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
    def location_circulation_authority(self) -> str:
        return self.p(
            self.get('content/locationCirculationAuthority'),
            "Weitere Angaben"
        )

    @property
    def registration_office(self) -> str:
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
    def text(self) -> str:
        return self.dedent(f"""
        {self.debtor}
        {self.affected_land}
        {self.location_circulation_authority}
        {self.information_about_edition}
        {self.days_after_publication}
        {self.entry_deadline}
        {self.appeal}
        {self.registration_office}
        {self.legal}
        {self.remarks}
        """)


class KK10(KK):

    @property
    def title(self) -> str:
        return self.get('content/title') or self.get('meta/title/de')

    @property
    def publication(self) -> str:
        return self.p(self.get('content/publication'))

    @property
    def text(self) -> str:
        return self.dedent(f"""
        {self.publication}
        {self.legal}
        {self.remarks}
        """)
