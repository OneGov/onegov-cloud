from collections import defaultdict
from datetime import datetime

from onegov.agency.collections import (
    ExtendedAgencyCollection, ExtendedPersonCollection)
from onegov.core.csv import CSVFile
from onegov.core.orm.abstract.adjacency_list import numeric_priority
from onegov.core.utils import linkify


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath
    from collections.abc import Callable
    from collections.abc import Mapping
    from datetime import date
    from onegov.agency.app import AgencyApp
    from onegov.agency.models import ExtendedAgency
    from onegov.agency.models import ExtendedPerson
    from onegov.agency.request import AgencyRequest
    from onegov.core.csv import DefaultRow
    from onegov.people import AgencyMembership
    from sqlalchemy.orm import Session
    from typing import TypeVar
    from typing_extensions import TypeVarTuple
    from typing_extensions import Unpack

    _T = TypeVar('_T')
    _Ts = TypeVarTuple('_Ts')


def with_open(
    func: 'Callable[[CSVFile[DefaultRow], Unpack[_Ts]], _T]'
) -> 'Callable[[StrOrBytesPath, Unpack[_Ts]], _T]':

    def _read(filename: 'StrOrBytesPath', *args: 'Unpack[_Ts]') -> '_T':
        with open(filename, 'rb') as f:
            file = CSVFile(
                f,
                encoding='iso-8859-1'
            )
            return func(file, *args)

    return _read


def v_(string: str | None) -> str | None:
    if not string or string == 'NULL' or not string.strip():
        return None
    return string.strip()


def cleaned(
    func: 'Callable[[str], _T]'
) -> 'Callable[[str | None], _T | None]':

    def clean(string: str | None) -> '_T | None':
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
    return string


# FIXME: use Markup
def p(text: str) -> str:
    return f'<p>{text}</p>'


# FIXME: use Markup
def br(text: str) -> str:
    return text + '<br>'


# FIXME: use Markup
def split_address_on_new_line(address: str, newline: bool = False) -> str:
    new_addr = '<br>'.join(part.strip() for part in address.split(','))
    new_addr = new_addr + '<br>' if newline else new_addr
    return new_addr


def get_address(line: 'DefaultRow') -> str | None:
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


# FIXME: use Markup
def get_agency_portrait(line: 'DefaultRow') -> str | None:
    portrait = ''
    address = get_address(line)
    if address:
        portrait += br(address)

    if v_(line.telzentrale):
        tel = linkify(get_phone(v_(line.telzentrale)))
        portrait += br(f"Tel.: {tel}")

    if v_(line.faxzentrale):
        tel = linkify(get_phone(v_(line.faxzentrale)))
        portrait += br(f"Fax: {tel}")

    if v_(line.emailneutral):
        portrait += br(f"{linkify(v_(line.emailneutral))}")

    homepage = v_(line.homepageurl)
    if homepage:
        portrait += br(f'<a href="{homepage}">Homepage</a>')

    stadtplanurl = v_(line.stadtplanurl)
    if stadtplanurl:
        portrait += br(f'<a href="{stadtplanurl}">Standort</a>')

    if v_(line.oeffnungszeiten):
        portrait += br(f"Öffnungszeiten:\n{v_(line.oeffnungszeiten)}")

    if v_(line.wahlperiode):
        portrait += br(f"Wahlperiode: {v_(line.wahlperiode)}")

    if v_(line.bemerkung):
        portrait += br(f"{v_(line.bemerkung)}")

    portrait = portrait.strip()
    return portrait and p(portrait) or None


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

    print('Treated as root agencies: ', ", ".join(treat_as_root))
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
            export_fields=["person.title", "person.phone"]
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

        note = "\n".join([
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

    print('Treated as root agencies: ', ", ".join(treat_as_root))
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
        f.write("\n".join(uq_person_not_found))
        f.write('\n\nAGENCIES NOT FOUND\n')
        f.write("\n".join((uq_agency_by_name_not_found)))
    print('Find the logfile in ' + log_file_path)


def import_membership_titles(
    agency_file: 'StrOrBytesPath',
    person_file: 'StrOrBytesPath',
    request: 'AgencyRequest',
    app: 'AgencyApp'
) -> None:

    agencies = parse_agencies(agency_file)
    match_person_membership_title(person_file, agencies, request, app)
