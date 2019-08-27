from dateutil.parser import parse
from onegov.gazette.models import Issue
from textwrap import dedent


def html_converter(text):
    return '<br>'.join((line.strip() for line in text.split('\n')))


class SogcConverter(object):

    """ The base class for all converters. """

    def __init__(self, root):
        self.root = root

    def get(self, path, converter=html_converter, root=None):
        root = root if root is not None else self.root
        result = root.find(path)
        result = result.text.strip() if result is not None else ''
        if converter and result != '':
            result = converter(result)
        return result

    def dedent(self, text):
        return dedent(text).strip().replace('\n', '')

    @property
    def title(self):
        return self.get('meta/title/de')

    @property
    def source(self):
        return self.get('meta/publicationNumber')

    @property
    def publication_date(self):
        return self.get('meta/publicationDate', converter=parse)

    @property
    def expiration_date(self):
        return self.get('meta/expirationDate', converter=parse)

    def issues(self, session):
        query = session.query(Issue.name)
        query = query.filter(Issue.date >= self.publication_date)
        query = query.order_by(Issue.date)
        query = query.first()
        return [query.name] if query else []

    def p(self, value, title="", title_break=True, subtitle="",
          subtitle_break=False, fmt=None):
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
    def addition(self):
        value = self.get('content/addition')
        if not value:
            return ""
        if value == 'legacy':
            return self.p("Erbschaft", "Zusatz")
        elif value == 'refusedLegacy':
            return self.p("ausgeschlagene Erbschaft", "Zusatz")
        elif value == 'custom':
            value = self.get('content/additionCustom')
            return self.p(value, "Zusatz")

    @property
    def comment_entry_deadline(self):
        return self.p(
            self.get('content/commentEntryDeadline'),
            "Kommentar zur Frist"
        )

    @property
    def days_after_publication(self):
        return self.p(
            self.get('content/daysAfterPublication', int),
            "Frist",
            fmt='days'
        )

    @property
    def debtor(self):
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
                        self.get('{path}/addressCustomText'),
                        self.get('{path}/country/name/de')
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

    @property
    def entry_deadline(self):
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
    def information_about_edition(self):
        return self.p(
            self.get('content/informationAboutEdition'),
            "Angaben zur Auflage"
        )

    @property
    def legal(self):
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
    def remarks(self):
        return self.p(
            self.get('content/remarks'),
            "Bemerkungen"
        )

    @property
    def registration_office(self):
        return self.p(
            self.get('content/registrationOffice'),
            "Anmeldestelle"
        )

    @property
    def resolution_date(self):
        return self.p(
            self.get('content/resolutionDate', parse),
            "Datum der Konkurseröffnung",
            fmt='date'
        )


class KK01(KK):

    @property
    def text(self):
        return self.dedent(f"""
        {self.debtor}
        {self.resolution_date}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK02(KK):

    @property
    def proceeding(self):
        value = self.get('content/proceeding/selectType')
        if not value:
            return ""
        if value == 'summary':
            return self.p("summarisch", "Art des Konkursverfahrens")
        elif value == 'ordinary':
            return self.p("ordentlich", "Art des Konkursverfahrens")
        elif value == 'other':
            value = self.get('content/otherProceeding')
            return self.p(value, "Art des Konkursverfahrens")

    @property
    def creditor_meeting(self):
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
    def text(self):
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
    def cessation_date(self):
        return self.p(
            self.get('content/cessationDate', parse),
            "Datum der Einstellung",
            fmt='date'
        )

    @property
    def advance_amount(self):
        return self.p(
            self.get('content/advanceAmount', float),
            "Betrag des Kostenvorschusses",
            fmt='currency'
        )

    @property
    def text(self):
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
    def claim_of_creditors(self):
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
    def inventory(self):
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
    def text(self):
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
    def location_circulation_authority(self):
        return self.p(
            self.get('content/locationCirculationAuthority'),
            "Angaben zur Auflage"
        )

    @property
    def text(self):
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
    def proceeding_end_date(self):
        return self.p(
            self.get('content/proceedingEndDate', parse),
            "Datum des Schlusses",
            fmt='date'
        )

    @property
    def text(self):
        return self.dedent(f"""
        {self.debtor}
        {self.proceeding_end_date}
        {self.addition}
        {self.legal}
        {self.remarks}
        """)


class KK07(KK):

    @property
    def proceeding_revocation_date(self):
        return self.p(
            self.get('content/proceedingRevocationDate', parse),
            "Datum des Widerrufs",
            fmt='date'
        )

    @property
    def text(self):
        return self.dedent(f"""
        {self.debtor}
        {self.proceeding_revocation_date}
        {self.legal}
        {self.remarks}
        """)


class KK08(KK):

    @property
    def auction(self):
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
    def auction_objects(self):
        return self.p(
            self.get('content/auctionObjects'),
            "Steigerungsobjekte"
        )

    @property
    def entry_start(self):
        return self.p(
            self.get('content/entryStart', parse),
            "Beginn der Frist",
            fmt='date'
        )

    @property
    def text(self):
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
    def affected_land(self):
        return self.p(
            self.get('content/affectedLand'),
            "Betroffenes Grundstück"
        )

    @property
    def appeal(self):
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
    def location_circulation_authority(self):
        return self.p(
            self.get('content/locationCirculationAuthority'),
            "Weitere Angaben"
        )

    @property
    def registration_office(self):
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
    def text(self):
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
    def title(self):
        return self.get('content/title') or self.get('meta/title/de')

    @property
    def publication(self):
        return self.p(self.get('content/publication'))

    @property
    def text(self):
        return self.dedent(f"""
        {self.publication}
        {self.legal}
        {self.remarks}
        """)
