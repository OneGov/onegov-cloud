import re
from datetime import datetime

import click

from onegov.core.cli import command_group
from onegov.core.csv import CSVFile
from onegov.translator_directory.constants import GENDERS, CERTIFICATES
from onegov.translator_directory.models.certificate import \
    LanguageCertificate
from onegov.translator_directory.models.translator import Language, Translator

cli = command_group()


def with_open(func):
    def _read(*args):
        with open(args[0], 'rb') as f:
            file = CSVFile(
                f,
                encoding='utf-8'
            )
            return func(file, *args[1:])
    return _read


skip_languages = ['-', 'Kein Einsatz']

# pattern that deals with languages containing commas within brackets
lang_split_pattern = re.compile(r',(?![^\(\[]*[\]\)])')


def parse_language_field(languages):
    """The fields can have commas in it, so we can not split by comma"""
    if not languages:
        return
    for lang in lang_split_pattern.split(languages):
        if not lang or lang in skip_languages:
            continue
        yield lang.strip()


@with_open
def import_languages(csvfile, session):
    all_languages = set()

    def add_languages(languages):
        for lang in parse_language_field(languages):
            all_languages.add(lang)

    for line in csvfile.lines:

        add_languages(line.muttersprache)
        add_languages(line.sprachen_wort)
        add_languages(line.sprachen_schrift)

    session.bulk_insert_mappings(
        Language, ({'name': name} for name in all_languages)
    )
    session.flush()
    click.secho(f'Imported {len(all_languages)} languages')


@with_open
def import_certifcates(csvfile, session):
    all_certs = set()

    def parse(certs):
        for cert in certs.split(', '):
            all_certs.add(cert.strip())

    for line in csvfile.lines:
        parse(line.zertifikate)

    session.bulk_insert_mappings(
        LanguageCertificate,
        ({'name': name} for name in all_certs)
    )

    session.flush()
    click.secho(f'Imported {len(all_certs)} certificates')


def parse_gender(field):
    if not field:
        return GENDERS[-1]
    if field == 'Männlich':
        return GENDERS[0]
    return GENDERS[1]


def parse_date(field):
    if field:
        return datetime.strptime(field, '%Y-%m-%d')


def parse_confirm_name_reveal(line):
    field = line.zustimmung_namensbekanntgabe
    if field or field == 'Ja':
        return True
    return False


def get_languages(names, session):
    if names is None:
        return
    langs = session.query(Language).filter(Language.name.in_(names)).all()
    assert len(langs) == len(names)
    return langs


def get_certificates(certs, session):
    if not certs:
        return []
    return session.query(LanguageCertificate).filter(
        LanguageCertificate.name.in_(certs)).all()


def parse_certificates(field):
    if not field or field == '-':
        return
    certs = field.split(', ')
    for cert in certs:
        if cert not in CERTIFICATES:
            raise ValueError(f"Can't import unknown certificate {field}")
    return certs


def parse_boolean(field):
    if field and field == 'Ja':
        return True
    return False


def parse_distance(field):
    if not field:
        return None
    return float(field)


def parse_phone(field):
    if not field or field == '-':
        return
    return field


@with_open
def import_translators(csvfile, session):
    count = 0
    for line in csvfile.lines:
        try:
            pers_id = int(line.personal_nr)
        except ValueError:
            pers_id = None

        assert line.name
        assert line.vorname
        count += 1
        trs = Translator()

        trs.pers_id = pers_id
        trs.last_name = line.name
        trs.first_name = line.vorname
        trs.gender = parse_gender(line.geschlecht)
        trs.date_of_birth = parse_date(line.geburtsdatum)
        trs.nationality = line.staatsangehorigkeit
        trs.address = line.adresse
        trs.zip_code = line.plz
        trs.city = line.ort
        trs.drive_distance = parse_distance(line.wegberechnung)
        trs.social_sec_number = line.ahv_nr
        trs.bank_name = line.bank_name
        trs.bank_address = line.bank_adresse
        trs.iban = line.iban
        trs.account_owner = line.bank_konto_lautet_auf
        trs.email = line.e_mail
        trs.tel_private = parse_phone(line.telefon_privat)
        trs.tel_mobile = parse_phone(line.natel)
        trs.tel_office = parse_phone(line.telefon_geschaft)
        trs.availability = line.erreich_und_verfugbarkeit
        trs.confirm_name_reveal = parse_confirm_name_reveal(line)
        trs.date_of_application = parse_date(line.bewerbung)
        trs.date_of_decision = parse_date(line.entscheid_datum)
        trs.occupation = line.berufliche_qualifikation_tatigkeit
        trs.proof_of_preconditions = parse_phone(
            line.nachweis_der_voraussetzungen)
        trs.agency_references = line.referenzen_behorden
        trs.education_as_interpreter = parse_boolean(
            line.ausbildung_ubersetzen_dolmetschen)
        trs.certificates = get_certificates(
            parse_certificates(line.zertifikate), session)
        trs.comments = line.bemerkungen
        trs.other_certificates = line.andere_zertifikate
        trs.operation_comments = line.besondere_hinweise_einsatzmoglichkeiten

        trs.mother_tongues = get_languages(
            tuple(parse_language_field(line.muttersprache)), session
        )
        trs.spoken_languages = get_languages(
            tuple(parse_language_field(line.sprachen_wort)), session)

        trs.written_languages = get_languages(
            tuple(parse_language_field(line.sprachen_wort)), session
        )

        session.add(trs)
        session.flush()

    click.secho(f'Imported {count} translators')


def clear_all_records(session):
    for translator in session.query(Translator):
        session.delete(translator)
    for certificate in session.query(LanguageCertificate):
        session.delete(certificate)
    for language in session.query(Language):
        session.delete(language)


def import_translator_file(session, path, clear):
    if clear:
        clear_all_records(session)
    import_certifcates(path, session)
    import_languages(path, session)
    import_translators(path, session)


@cli.command(name='import', context_settings={'singular': True})
@click.option('--path', required=True)
@click.option('--clear', is_flag=True)
def do_import(path, clear):

    def execute(request, app):
        return import_translator_file(request.session, path, clear)
    return execute
