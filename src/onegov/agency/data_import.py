import csv
from uuid import uuid4

from onegov.agency.models import ExtendedPerson, ExtendedAgency
from onegov.core.csv import CSVFile
from onegov.core.utils import normalize_for_url


def rewrite_without_empty_lines(fp, mod_fp):
    with open(fp, 'r', encoding='iso-8859-1') as f:
        with open(mod_fp, "w", encoding='iso-8859-1') as ff:
            writer = csv.writer(ff, delimiter=";")
            for line in csv.reader(f, delimiter=";"):
                if not line:
                    continue
                else:
                    writer.writerow(line)

def with_open(func):
    def _read(*args):
        with open(args[0], 'rb') as f:
            file = CSVFile(
                f,
                encoding='iso-8859-1'
            )
            return func(file, *args[1:])
    return _read


@with_open
def import_bs_agencies(csvfile, request):
    session = request.session
    agencies = {}

    all_lines = list(csvfile.lines)

    for header in csvfile.headers:
        print(header)

    assert False


@with_open
def import_bs_persons(csvfile, request):
    session = request.session
    persons = {}

    all_lines = list(csvfile.lines)

    for header in csvfile.headers:
        print(header)

    assert False

@with_open
def import_bs_data_file(csvfile, request):
    persons = {}
    agencies = {}
    memberships = {}
    session = request.session

    all_lines = list(csvfile.lines)

    for line in all_lines:

        url = line.url1.strip()
        url2 = line.url2.strip()

        active = line.pers__aktiv == '1' or False
        note = ""
        if line.bemerkung:
            note = line.bemerkung

        if url2 and url2 != url:
            note += f"\n {url2}"
        if line.amstdauervon:
            bis = line.amstdauerbis or ''
            note += f"\nAmtsdauer {line.amstdauervon} - {bis}"

        if line.sprechstunde:
            note += f"\nSprechstunde: {line.sprechstunde}"

        # first two keywords are the names
        # keywords just contain information collection from other fields
        # keywords = line.stichworte.split(";")[2:]
        # if keywords:
        #     note += "\n".join(keywords)

        persons.setdefault(line.personid, ExtendedPerson(
            id=uuid4(),
            last_name=line.name,
            first_name=line.vorname,
            salutation=line.anrede or None,
            academic_title=line.titel or None,
            function=line.funktion or None,
            email=line.email or None,
            phone=line.telextern or None,
            phone_direct=line.telmobil or None,
            website=url or None,
            notes=note or None,
            born=line.geburtsdatum or None,
            political_party=line.partei or None,
            address=line.privatadresse or None,
            access=line.suchbar == '1' and 'public' or 'secret'
        ))
        # agency_active = line.oe_aktiv == '1' or False
        agency = agencies.setdefault(line.oe_id, ExtendedAgency(
            title=line.oe_bezeichnung,
            name=normalize_for_url(line.oe_bezeichnung)
        ))
        memberships_by_oe = memberships.setdefault(line.oe_id, set())
        memberships_by_oe.add(line.personid)

    session.add_all(persons.values())
    session.add_all(agencies.values())
    session.flush()

    for orig_id, agency in agencies.items():
        members = memberships[orig_id]
        for pers_id in members:
            person = persons[pers_id]
            agency.add_person(person.id, person.function)
    #
    # session.flush()
    assert False