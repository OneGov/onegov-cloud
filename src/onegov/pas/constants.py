from __future__ import annotations

# Other constants


# There might come a time where we have to changes this but at least we have
# the safeguard to not import something totally unexpected (e.g. reading the
# wrong key)
from __future__ import annotations

COMMON_PARTY_NAMES = (
    'ALG',
    'CSP',
    'Die Mitte',
    'FDP',
    'GLP',
    'CVP',
    'Parteilos',
    'Piratenpartei',
    'SP',
    'SVP',
)

"""
These values were obtained by running the following command:

    onegov-pas --select '/onegov_pas/zug' import-commission-data \
        "name_of_commission.xlsx"

And then, inside the preprocess* function printing out the `header_row.`
"""

commission_expected_headers_variant_1 = [
    'ID',
    'Personalnummer',
    'Vertragsnummer',
    'Geschlecht',
    'Vorname',
    'Nachname',
    'Versandart',
    'Versand-Adresse',
    'Versand-Adresszusatz',
    'Versand-PLZ',
    'Versand-Ort',
    'Privat-Adresse',
    'Privat-Adresszusatz',
    'Privat-PLZ',
    'Privat-Ort',
    'Rolle Kommission',
    'Partei',
    'Fraktion',
    'Wahlkreis',
    'Eintritt Kommission',
    'Austritt Kommission',
    'Zusatzinformationen',
    'Geburtsdatum',
    'Bürgerort',
    'Beruf',
    'Akademischer Titel',
    'Anrede',
    'Adress-Anrede',
    'Brief-Anrede',
    'Spedition KR-Vorlagen',
    'Telefon Privat',
    'Telefon Mobile',
    'Telefon Geschäft',
    '1. E-Mail',
    '2. E-Mail',
    'Webseite',
    'Bemerkungen',
]

# there is another type of commission import header row, which differs in
# the headers diff:
# Austritt, Eintritt, Funktion, Im Kantonsrat seit, Kantonsrat Funktion,
# Rolle, q


commission_expected_headers_variant_2 = [
    'q',  # +
    'Personalnummer',
    'Vertragsnummer',
    'Geschlecht',
    'Vorname',
    'Nachname',
    'Versandart',
    'Versand-Adresse',
    'Versand-Adresszusatz',
    'Versand-PLZ',
    'Versand-Ort',
    'Privat-Adresse',
    'Privat-Adresszusatz',
    'Privat-PLZ',
    'Privat-Ort',
    'Rolle',  # + Parliamenarian Role, needs more: Stv.Landschreiberin
    'Funktion',
    'Kantonsrat Funktion',  # +
    'Im Kantonsrat seit',
    'Partei',
    'Fraktion',
    'Wahlkreis',
    'Eintritt',  # +
    'Austritt',  # +
    'Zusatzinformationen',
    'Geburtsdatum',
    'Bürgerort',
    'Beruf',
    'Akademischer Titel',
    'Anrede',
    'Adress-Anrede',
    'Brief-Anrede',
    'Spedition KR-Vorlagen',
    'Telefon Privat',
    'Telefon Mobile',
    'Telefon Geschäft',
    '1. E-Mail',
    '2. E-Mail',
    'Webseite',
    'Bemerkungen',
]

# fixme: incomplete, these needs mapping and implementation
diff = [
    'Austritt',
    'Eintritt',
    'Funktion',
    'Im Kantonsrat seit',
    'Kantonsrat',
    'Funktion',
    'Rolle',
    'q',
]
