from collections import defaultdict
from datetime import datetime


from onegov.agency.collections import ExtendedAgencyCollection, \
    ExtendedPersonCollection
from onegov.agency.models import ExtendedAgencyMembership
from onegov.core.csv import CSVFile


def with_open(func):
    def _read(*args):
        with open(args[0], 'rb') as f:
            file = CSVFile(
                f,
                encoding='utf-16'
            )
            return func(file, *args[1:])
    return _read


def get_agency_portrait(line):
    portrait = ''
    if line.postadresse:
        portrait += line.postadresse
    if line.offnungszeiten:
        portrait += f"\nÖffnungszeiten: {line.offnungszeiten}"
    if line.homepage:
        portrait += f"\n\n{line.homepage}"
    portrait = portrait.strip()
    return portrait and f'<p>{portrait}</p>' or None


@with_open
def import_bs_agencies(csvfile, session):
    agencies = ExtendedAgencyCollection(session)
    lines_by_id = {line.basisid: line for line in csvfile.lines}
    treat_as_root = tuple(
        line.basisparentid for line in csvfile.lines
        if line.basisparentid not in lines_by_id.keys()
    )
    added_agencies = {}
    children = defaultdict(list)
    roots = []

    print('Treated as root agencies: ', ", ".join(treat_as_root))
    for line in csvfile.lines:
        parent_id = line.basisparentid or None
        basisid = line.basisid
        if parent_id:
            if parent_id in treat_as_root:
                parent_id = None
                roots.append(basisid)
            children[parent_id].append(basisid)

    def parse_agency(line, parent=None):
        agency = agencies.add(
            parent=parent,
            title=line.bezeichnung,
            description=line.kurzbezeichnung or None,
            portrait=get_agency_portrait(line)
        )
        added_agencies[line.basisid] = agency
        return agency

    def add_children(basisid, parent=None):
        line = lines_by_id[basisid]
        agency = parse_agency(line, parent=parent)
        for child_id in children.get(line.basisid, []):
            add_children(child_id, parent=agency)

    for basisid in roots:
        add_children(basisid)
    return added_agencies


@with_open
def import_bs_persons(csvfile, agencies, session):
    persons = {}
    people = ExtendedPersonCollection(session)

    def parse_date(date_string):
        if not date_string:
            return None
        return datetime.strptime(date_string, '%d.%m.%Y').date()

    def parse_person(line):
        note = ""
        if line.bemerkung:
            note = line.bemerkung

        assert line.basisid not in persons
        person_ = people.add(
            last_name=line.name,
            first_name=line.vorname,
            salutation=line.anrede or None,
            academic_title=line.titel or None,
            function=line.funktion or None,
            email=line.email or None,
            phone=line.telextern or None,
            phone_direct=line.telmobile or None,
            website=None,
            notes=note or None,
            born=None,
            political_party=None,
            address=None,
            access='public'
        )
        persons[line.basisid] = person_

        # A person has only one membership
        if line.basis_orgeinheitid:
            parent_id = line.basis_orgeinheitid
            agency = agencies.get(parent_id)
            if agency:
                person_.memberships.append(
                    ExtendedAgencyMembership(
                        agency_id=agency.id,
                        title="",
                        since=parse_date(line.eintrittsdatum),
                        prefix=None,
                        addition=None,
                        note=None,
                        order_within_agency=0,
                        order_within_person=0
                    )
                )
            else:
                print(f'agency id {parent_id} not found in agencies')

    for line in csvfile.lines:
        parse_person(line)
    return persons


def import_bs_data(agency_file, person_file, request):
    session = request.session
    agencies = import_bs_agencies(agency_file, session)
    persons = import_bs_persons(person_file, agencies, session)
    return agencies, persons
