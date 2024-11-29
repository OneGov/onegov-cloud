from collections import defaultdict
from datetime import datetime

from email_validator import validate_email, EmailNotValidError, \
    EmailUndeliverableError
from markupsafe import Markup

from onegov.agency.collections import (
    ExtendedAgencyCollection, ExtendedPersonCollection)
from onegov.core.csv import CSVFile
from onegov.core.orm.abstract.adjacency_list import numeric_priority
from onegov.core.utils import linkify

from typing import TypeVar, Any
from typing import TypeVarTuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath
    from collections.abc import Callable, Iterable
    from collections.abc import Mapping
    from datetime import date
    from onegov.agency.app import AgencyApp
    from onegov.agency.models import ExtendedAgency
    from onegov.agency.models import ExtendedPerson
    from onegov.agency.request import AgencyRequest
    from onegov.core.csv import DefaultRow
    from onegov.people import AgencyMembership
    from sqlalchemy.orm import Session

T = TypeVar('T')
Ts = TypeVarTuple('Ts')


def with_open(
    func: 'Callable[[CSVFile[DefaultRow], *Ts], T]'
) -> 'Callable[[StrOrBytesPath, *Ts], T]':

    def _read(filename: 'StrOrBytesPath', *args: *Ts) -> T:
        with open(filename, 'rb') as f:
            file = CSVFile(
                f,
                # encoding='iso-8859-1'
                encoding='utf-8',  # lu
            )
            return func(file, *args)

    return _read


def v_(string: str | None) -> str | None:
    if not string or string == 'NULL' or not string.strip():
        return None
    return string.strip()


def cleaned(
    func: 'Callable[[str], T]'
) -> 'Callable[[str | None], T | None]':

    def clean(string: str | None) -> T | None:
        cleaned = v_(string)
        if not cleaned:
            return None
        return func(cleaned)

    return clean


@cleaned
def get_phone(string: str) -> str:
    if string.startswith('00'):
        return string.replace('00', '+', 1)
    if not string.startswith('+'):
        if len(string.replace(' ', '')) == 10:  # be sure #digits fit CH
            return string.replace('0', '+41 ', 1)
        # lu adds country digits
        if len(string.replace(' ', '')) == 9:
            return f'+41{string}'
    return string


def p(text: str) -> Markup:
    return Markup('<p>{}</p>').format(text)


def br(text: str) -> Markup:
    return Markup('{}<br>').format(text)


def split_address_on_new_line(
    address: str,
    newline: bool = False
) -> Markup:
    new_addr = Markup('<br>').join(part.strip() for part in address.split(','))
    new_addr = new_addr + Markup('<br>') if newline else new_addr
    return new_addr


def get_address(line: 'DefaultRow') -> Markup | None:
    stao_addr, post_addr = v_(line.standortadresse), v_(line.postadresse)
    if stao_addr and post_addr:
        if stao_addr == post_addr:
            return br(split_address_on_new_line(stao_addr))
        else:
            return br(split_address_on_new_line(stao_addr, True)) + br(
                split_address_on_new_line(post_addr)
            )
    elif stao_addr:
        return br(split_address_on_new_line(stao_addr))
    if post_addr:
        return br(split_address_on_new_line(post_addr))
    return None


def get_agency_portrait(line: 'DefaultRow') -> Markup | None:
    portrait = Markup('')
    address = get_address(line)
    if address:
        portrait += br(address)

    if v_(line.telzentrale):
        tel = linkify(get_phone(v_(line.telzentrale)))
        portrait += br(Markup('Tel.: {}').format(tel))

    if v_(line.faxzentrale):
        tel = linkify(get_phone(v_(line.faxzentrale)))
        portrait += br(Markup('Fax: {}').format(tel))

    if v_(line.emailneutral):
        portrait += br(linkify(v_(line.emailneutral)))

    homepage = v_(line.homepageurl)
    if homepage:
        portrait += br(Markup('<a href="{}">Homepage</a>').format(homepage))

    stadtplan = v_(line.stadtplanurl)
    if stadtplan:
        portrait += br(Markup('<a href="{}">Standort</a>').format(stadtplan))

    if v_(line.oeffnungszeiten):
        portrait += br(f'Öffnungszeiten:\n{v_(line.oeffnungszeiten)}')

    if v_(line.wahlperiode):
        portrait += br(f'Wahlperiode: {v_(line.wahlperiode)}')

    if v_(line.bemerkung):
        portrait += br(f'{v_(line.bemerkung)}')

    portrait = portrait.strip()
    return p(portrait) if portrait else None


@with_open
def import_bs_agencies(
    csvfile: CSVFile['DefaultRow'],
    session: 'Session',
    app: 'AgencyApp'
) -> dict[str, 'ExtendedAgency']:

    agencies = ExtendedAgencyCollection(session)
    lines_by_id = {line.verzorgeinheitid: line for line in csvfile.lines}
    treat_as_root = tuple(
        line.verzorgeinheitid for line in csvfile.lines
        if line.verzvorfahreoeid not in lines_by_id.keys()
    )
    if len(treat_as_root) == 1:
        # Use the first level as root
        treat_as_root = tuple(
            line.verzorgeinheitid for line in csvfile.lines
            if line.verzvorfahreoeid in treat_as_root
        )
    added_agencies = {}
    children = defaultdict(list)
    roots = []
    added_count = 0

    print('Treated as root agencies: ', ', '.join(treat_as_root))
    for line in csvfile.lines:
        parent_id = line.verzvorfahreoeid or None
        basisid = line.verzorgeinheitid

        if parent_id:
            if basisid in treat_as_root:
                parent_id = None
                roots.append(basisid)
            children[parent_id].append(basisid)

    def parse_agency(
        line: 'DefaultRow',
        parent: 'ExtendedAgency | None' = None
    ) -> 'ExtendedAgency':

        portrait = get_agency_portrait(line)
        agency = agencies.add(
            parent=parent,
            title=line.bezeichnung.strip(),
            description=None,
            portrait=portrait,
            order=numeric_priority(v_(line.anzeigeprio)),
            export_fields=['person.title', 'person.phone']
        )
        added_agencies[line.verzorgeinheitid] = agency
        return agency

    def add_children(
        basisid: str,
        parent: 'ExtendedAgency | None' = None
    ) -> None:

        nonlocal added_count
        added_count += 1
        if added_count % 50 == 0:
            app.es_indexer.process()
            app.psql_indexer.bulk_process(session)
        line = lines_by_id[basisid]
        agency = parse_agency(line, parent=parent)
        for child_id in children.get(line.verzorgeinheitid, []):
            add_children(child_id, parent=agency)

    for basisid in roots:
        add_children(basisid)
    return added_agencies


@with_open
def import_bs_persons(
    csvfile: CSVFile['DefaultRow'],
    agencies: 'Mapping[str, ExtendedAgency]',
    session: 'Session',
    app: 'AgencyApp'
) -> list['ExtendedPerson']:

    people = ExtendedPersonCollection(session)
    persons = []

    def parse_date(date_string: str | None) -> 'date | None':
        if not date_string:
            return None
        return datetime.strptime(date_string, '%d.%m.%Y').date()

    def parse_person(line: 'DefaultRow') -> None:
        bemerkung = v_(line.bemerkung)
        notiz = v_(line.notiz)
        sprechstunde = v_(line.sprechstunde)

        note = '\n'.join([
            s for s in (bemerkung, notiz, sprechstunde) if s]
        )

        agency_id = line.verzorgeinheitid

        person_ = people.add(
            last_name=v_(line.name) or 'NACHNAME',
            first_name=v_(line.vorname) or 'VORNAME',
            salutation=v_(line.anrede),
            academic_title=v_(line.titel),
            function=v_(line.funktion),
            email=v_(line.email),
            phone=get_phone(line.telextern),
            phone_direct=get_phone(line.telmobil),
            website=v_(line.url1) or v_(line.url2) or None,
            notes=note or None,
            born=v_(line.geburtsdatum),
            political_party=v_(line.partei),
            address=v_(line.privatadresse),
            access='public'
        )
        persons.append(person_)

        # A person has only one membership
        if agency_id:
            agency = agencies.get(agency_id)
            if agency:
                agency.add_person(
                    person_.id,
                    title='Mitglied',
                    since=None,
                    prefix=None,
                    addition=None,
                    note=None,
                )

            else:
                print(f'agency id {agency_id} not found in agencies')

    for ix, line in enumerate(csvfile.lines):
        if ix % 50 == 0:
            app.es_indexer.process()
            app.psql_indexer.bulk_process(session)
        parse_person(line)

    return persons


def import_bs_data(
    agency_file: 'StrOrBytesPath',
    person_file: 'StrOrBytesPath',
    request: 'AgencyRequest',
    app: 'AgencyApp'
) -> tuple[dict[str, 'ExtendedAgency'], list['ExtendedPerson']]:

    session = request.session
    agencies = import_bs_agencies(agency_file, session, app)
    persons = import_bs_persons(person_file, agencies, session, app)

    for agency in agencies.values():
        agency.sort_relationships()

    return agencies, persons


def get_plz_city(plz: str | None, ort: str | None) -> str | None:
    if plz and ort:
        return f'{plz} {ort}'

    if ort:
        return ort

    if plz:
        return plz

    return None


def get_web_address(internet_adresse: str) -> str | None:
    if not internet_adresse:
        return None

    if internet_adresse.startswith('http'):
        return internet_adresse

    return f'http://{internet_adresse}'


def get_email(line: 'DefaultRow') -> str | None:
    email = v_(line.e_mail_adresse)

    if not email:
        return None

    # only keep valid generic email address, but not `vorname.nachname@lu.ch`
    addr = email.split(' ')
    for a in addr:
        if a in ['vorname.name@lu.ch', '@lu.ch']:
            continue
        if '@' in a:
            try:
                validate_email(a)
            except EmailUndeliverableError:
                continue
            except EmailNotValidError:
                print(f'Error importing person with invalid email {a}; line '
                      f'{line.rownumber}')
                continue

            return a

    return None


def check_skip(line: 'DefaultRow') -> bool:
    if line.department == 'zNeu':
        return True

    if any(s in line.vorname for s in ('Zi.', 'Korr.', 'test')):
        return True

    if any(s in line.nachname for s in ('WG', 'WH', 'W3', 'W5',
                                        'frei neuer MA', 'frei  neuer MA',
                                        'AAL Picket')):
        return True

    if line.nachname == '' and line.vorname == '':
        return True  # skip empty lines

    if line.vorname and line.vorname[-1].isdigit():
        print(f'Error importing person with digit in first name; line '
              f'{line.rownumber}, {line.vorname}')
        return True

    return False


def check_skip_people(line: 'DefaultRow') -> bool:
    kw = 'Telefon'
    if kw in line.nachname or kw in line.vorname or kw in line.funktion:
        return True

    return False


def agency_id_agency_lu(words: 'Iterable[Any]') -> str:
    """
    Generates an agency id based on each organisation and sub organisation word
    """
    return '__'.join(str(word).lower() for word in words if word)


def agency_id_person_lu(line: 'DefaultRow') -> str:
    """
    Generates an agency id based on each organisation and sub organisation
    name for a person.
    """
    words = [line.department, line.dienststelle, line.abteilung,
             line.unterabteilung, line.unterabteilung_2]
    return agency_id_agency_lu(words)


@with_open
def import_lu_people(
    csvfile: CSVFile['DefaultRow'],
    agencies: 'Mapping[str, ExtendedAgency]',
    session: 'Session',
    app: 'AgencyApp'
) -> list['ExtendedPerson']:

    people = ExtendedPersonCollection(session)
    persons = []

    def parse_person(line: 'DefaultRow') -> None:
        agency_id = agency_id_person_lu(line)
        hi_code = v_(line.hi_code)
        order = 0 if not hi_code else int(hi_code)

        person_ = people.add(
            last_name=v_(line.nachname) or ' ',
            first_name=v_(line.vorname) or ' ',
            salutation=None,
            academic_title=v_(line.akad__titel),
            function=v_(line.funktion),
            email=get_email(line),
            phone=get_phone(line.isdn_nummer),
            phone_direct=get_phone(line.mobil),
            website=v_(get_web_address(line.internet_adresse)),
            location_address=v_(line.adresse),
            location_code_city=v_(get_plz_city(line.plz, line.ort)),
            access='public'
        )
        persons.append(person_)

        if agency_id:
            agency = agencies.get(agency_id, None)
            if agency and order:
                agency.add_person(person_.id,
                                  title=person_.function or 'Mitglied',
                                  order_within_agency=order)
            elif agency:
                agency.add_person(person_.id,
                                  title=person_.function or 'Mitglied')
            else:
                print(f'Error agency id {agency_id} not found')

    for ix, line in enumerate(csvfile.lines):
        if ix % 100 == 0:
            app.es_indexer.process()
            app.psql_indexer.bulk_process(session)

        if not check_skip(line) and not check_skip_people(line):
            parse_person(line)

    return persons


@with_open
def import_lu_agencies(
    csvfile: CSVFile['DefaultRow'],
    session: 'Session',
    app: 'AgencyApp'
) -> dict[str, 'ExtendedAgency']:

    added_agencies = {}
    agencies = ExtendedAgencyCollection(session)

    # Hierarchy: Hierarchie: Department, Dienststelle, Abteilung,
    # Unterabteilung, Unterabteilung 2, Unterabteilung 3
    for ix, line in enumerate(csvfile.lines):
        if ix % 100 == 0:
            app.es_indexer.process()
            app.psql_indexer.bulk_process(session)

        if check_skip(line):
            continue

        dienststelle, abteilung, unterabteilung, unterabteilung_2 = (
            None, None, None, None)
        export_fields = ['person.title', 'person.phone']

        adr, pc, loc = None, None, None
        phone, phone_u2, phone_u, phone_a, phone_ds, phone_dep = \
            None, None, None, None, None, None
        kw = 'Telefon'
        if kw in line.nachname or kw in line.vorname or kw in line.funktion:
            print(f'*** tschupre found org phone on csv line {line.rownumber}')
            phone = get_phone(line.isdn_nummer)
            if v_(line.unterabteilung_2):
                phone_u2 = phone
            elif v_(line.unterabteilung):
                phone_u = phone
            elif v_(line.abteilung):
                phone_a = phone
            elif v_(line.dienststelle):
                phone_ds = phone
            elif v_(line.department):
                phone_dep = phone
            adr = v_(line.adresse)
            pc = v_(line.plz)
            loc = v_(line.ort)

        department_name = v_(line.department)
        if department_name:
            department = agencies.add_or_get(
                None, department_name, export_fields=export_fields)
            if phone_dep:
                department.phone = phone_dep
                department.location_address = adr
                department.location_code_city = get_plz_city(pc, loc)
            agency_id = agency_id_agency_lu([department_name])
            if agency_id not in added_agencies:
                added_agencies[agency_id] = department

        dienststellen_name = v_(line.dienststelle)
        if dienststellen_name:
            assert department, (f'Error adding agency with no department; '
                                f'line {line.rownumber}, {line.nachname}')
            dienststelle = agencies.add_or_get(
                department, dienststellen_name, export_fields=export_fields)
            if phone_ds:
                dienststelle.phone = phone_ds
                dienststelle.location_address = adr
                dienststelle.location_code_city = get_plz_city(pc, loc)
            agency_id = agency_id_agency_lu([
                department_name, dienststellen_name])
            if agency_id not in added_agencies:
                added_agencies[agency_id] = dienststelle

        abteilungs_name = v_(line.abteilung)
        if abteilungs_name:
            assert dienststelle, (f'Error adding agency with no dienststelle; '
                                  f'line {line.rownumber}, {line.nachname}')
            abteilung = agencies.add_or_get(
                dienststelle, abteilungs_name, export_fields=export_fields)
            if phone_a:
                abteilung.phone = phone_a
                abteilung.location_address = adr
                abteilung.location_code_city = get_plz_city(pc, loc)
            agency_id = agency_id_agency_lu([
                department_name, dienststellen_name, abteilungs_name])
            if agency_id not in added_agencies:
                added_agencies[agency_id] = abteilung

        unterabteilungs_name = v_(line.unterabteilung)
        if unterabteilungs_name:
            assert abteilung, (f'Error adding agency with no abteilung; '
                               f'line {line.rownumber}, {line.nachname}')
            unterabteilung = (
                agencies.add_or_get(abteilung, unterabteilungs_name,
                                    export_fields=export_fields))
            if phone_u:
                unterabteilung.phone = phone_u
                unterabteilung.location_address = adr
                unterabteilung.location_code_city = get_plz_city(pc, loc)
            agency_id = agency_id_agency_lu([
                department_name, dienststellen_name, abteilungs_name,
                 unterabteilungs_name])
            if agency_id not in added_agencies:
                added_agencies[agency_id] = unterabteilung

        unterabteilung_2_name = v_(line.unterabteilung_2)
        if unterabteilung_2_name:
            assert unterabteilung, \
                (f'Error adding agency with no unterabteilung; '
                 f'line {line.rownumber}, {line.nachname}')
            unterabteilung_2 = (
                agencies.add_or_get(unterabteilung, unterabteilung_2_name,
                                    export_fields=export_fields))
            if phone_u2:
                unterabteilung_2.phone = phone_u2
                unterabteilung_2.location_address = adr
                unterabteilung_2.location_code_city = get_plz_city(pc, loc)
            agency_id = agency_id_agency_lu([
                department_name, dienststellen_name, abteilungs_name,
                unterabteilungs_name, unterabteilung_2_name])
            if agency_id not in added_agencies:
                added_agencies[agency_id] = unterabteilung_2

    return added_agencies


def import_lu_data(
    data_file: 'StrOrBytesPath',
    request: 'AgencyRequest',
    app: 'AgencyApp'
) -> tuple[dict[str, 'ExtendedAgency'], list['ExtendedPerson']]:

    session = request.session
    agencies = import_lu_agencies(data_file, session, app)
    people = import_lu_people(data_file, agencies, session, app)

    return agencies, people


@with_open
def parse_agencies(csvfile: CSVFile['DefaultRow']) -> dict[str, str]:
    lines_by_id = {line.verzorgeinheitid: line for line in csvfile.lines}
    treat_as_root = tuple(
        line.verzorgeinheitid for line in csvfile.lines
        if line.verzvorfahreoeid not in lines_by_id.keys()
    )
    if len(treat_as_root) == 1:
        # Use the first level as root
        treat_as_root = tuple(
            line.verzorgeinheitid for line in csvfile.lines
            if line.verzvorfahreoeid in treat_as_root
        )
    added_agencies = {}

    print('Treated as root agencies: ', ', '.join(treat_as_root))
    for line in csvfile.lines:
        basisid = line.verzorgeinheitid
        added_agencies[basisid] = line.bezeichnung.strip()

    return added_agencies


@with_open
def match_person_membership_title(
    csvfile: CSVFile['DefaultRow'],
    agencies: 'Mapping[str, str]',
    request: 'AgencyRequest',
    app: 'AgencyApp'
) -> None:

    session = request.session
    people = ExtendedPersonCollection(session)
    agency_coll = ExtendedAgencyCollection(session)
    person_query = session.query(people.model_class)

    total_entries = 0
    person_not_found = []
    agency_by_name_not_found = []
    updated_memberships = []

    def find_persons(line: 'DefaultRow') -> list['ExtendedPerson']:
        nonlocal person_not_found

        email = v_(line.email)
        fn = v_(line.vorname)
        ln = v_(line.name)

        persons = []

        if email:
            persons = person_query.filter(people.model_class.email.in_(
                (email, email.lower())
            )).all()
        if not persons and fn and ln:
            persons = person_query.filter(
                people.model_class.first_name == fn,
                people.model_class.last_name == ln
            ).all()
        if not persons:
            person_not_found.append(f'{email}, {fn} {ln}')
        return persons

    def get_agencies_by_name(name: str) -> list['ExtendedAgency']:
        return agency_coll.query().filter_by(title=name).all()

    def match_membership_title(
        line: 'DefaultRow',
        agencies: 'Mapping[str, str]'
    ) -> None:

        nonlocal agency_by_name_not_found

        persons = find_persons(line)
        agency_id = line.verzorgeinheitid
        if not persons:
            return
        if agency_id not in agencies:
            # actually we don't come here with our data for a solid export
            return

        agency_name = agencies[agency_id]
        agencies_by_name = get_agencies_by_name(agency_name)

        if not agencies_by_name:
            agency_by_name_not_found.append(agency_name)
            return

        def set_membership_title(
            membership: 'AgencyMembership',
            name: str | None
        ) -> None:
            nonlocal updated_memberships

            title = membership.title.strip()
            name = name.strip() if name else None

            if not name:
                if title:
                    # print('No function given but title set')
                    return
                membership.title = 'Mitglied'
                updated_memberships.append(membership)
                return

            if title and title != 'Mitglied':
                # title already set
                return

            membership.title = name
            updated_memberships.append(membership)

        function = v_(line.funktion)
        for person in persons:
            for membership in person.memberships:
                agency = membership.agency
                if agency in agencies_by_name:
                    set_membership_title(membership, function)

    for ix, line in enumerate(csvfile.lines):
        if ix % 50 == 0:
            app.es_indexer.process()
            app.psql_indexer.bulk_process(session)
        total_entries += 1
        match_membership_title(line, agencies)

    uq_person_not_found = set(person_not_found)
    uq_agency_by_name_not_found = set(agency_by_name_not_found)

    print('---- STATISTICS ----')
    print('Total rows: ', total_entries)
    print('Unique People not found: ', len(uq_person_not_found))
    print(
        'Unique Agencies by name not found: ',
        len(uq_agency_by_name_not_found)
    )
    print('Updated memberships: ', len(updated_memberships))

    log_file_path = '/var/lib/onegov-cloud/staka_bs_memberships_title.log'
    with open(str(log_file_path), 'w') as f:
        f.write('PEOPLE NOT FOUND\n')
        f.write('\n'.join(uq_person_not_found))
        f.write('\n\nAGENCIES NOT FOUND\n')
        f.write('\n'.join(uq_agency_by_name_not_found))
    print('Find the logfile in ' + log_file_path)


def import_membership_titles(
    agency_file: 'StrOrBytesPath',
    person_file: 'StrOrBytesPath',
    request: 'AgencyRequest',
    app: 'AgencyApp'
) -> None:

    agencies = parse_agencies(agency_file)
    match_person_membership_title(person_file, agencies, request, app)
