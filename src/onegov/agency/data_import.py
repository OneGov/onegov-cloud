from collections import defaultdict
from datetime import datetime

from onegov.agency.collections import ExtendedAgencyCollection, \
    ExtendedPersonCollection
from onegov.core.csv import CSVFile
from onegov.core.orm.abstract.adjacency_list import numeric_priority
from onegov.core.utils import linkify


def with_open(func):
    def _read(*args):
        with open(args[0], 'rb') as f:
            file = CSVFile(
                f,
                encoding='iso-8859-1'
            )
            return func(file, *args[1:])
    return _read


def v_(string):
    if not string or string == 'NULL' or not string.strip():
        return None
    return string.strip()


def cleaned(func):
    def clean(string):
        cleaned = v_(string)
        if not cleaned:
            return None
        return func(cleaned)
    return clean


@cleaned
def get_phone(string):
    if string.startswith('00'):
        return string.replace('00', '+', 1)
    if not string.startswith('+'):
        if len(string.replace(' ', '')) == 10:  # be sure #digits fit CH
            return string.replace('0', '+41 ', 1)
    return string


def p(text):
    return f'<p>{text}</p>'


def br(text):
    return text + '<br>'


def split_address_on_new_line(address, newline=False):
    new_addr = '<br>'.join(part.strip() for part in address.split(','))
    new_addr = new_addr + '<br>' if newline else new_addr
    return new_addr


def get_address(line):
    stao_addr, post_addr = v_(line.standortadresse), v_(line.postadresse)
    if stao_addr and post_addr:
        if stao_addr == post_addr:
            return br(split_address_on_new_line(stao_addr))
        else:
            return br(split_address_on_new_line(stao_addr, True)) +\
                   br(split_address_on_new_line(post_addr))
    elif stao_addr:
        return br(split_address_on_new_line(stao_addr))
    if post_addr:
        return br(split_address_on_new_line(post_addr))


def get_agency_portrait(line):
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
def import_bs_agencies(csvfile, session, app):
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

    def parse_agency(line, parent=None):
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

    def add_children(basisid, parent=None):
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
def import_bs_persons(csvfile, agencies, session, app):
    people = ExtendedPersonCollection(session)
    persons = []

    def parse_date(date_string):
        if not date_string:
            return None
        return datetime.strptime(date_string, '%d.%m.%Y').date()

    def parse_person(line):
        bemerkung = v_(line.bemerkung)
        notiz = v_(line.notiz)
        sprechstunde = v_(line.sprechstunde)

        note = "\n".join([
            s for s in (bemerkung, notiz, sprechstunde) if s]
        )

        if sprechstunde:
            note += f"\n{sprechstunde}"

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


def import_bs_data(agency_file, person_file, request, app):
    session = request.session
    agencies = import_bs_agencies(agency_file, session, app)
    persons = import_bs_persons(person_file, agencies, session, app)

    for agency in agencies.values():
        agency.sort_relationships()

    return agencies, persons
