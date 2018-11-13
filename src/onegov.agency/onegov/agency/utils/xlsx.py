from io import BytesIO
from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from xlsxwriter.workbook import Workbook


def export_to_xlsx(request, file):
    session = request.session
    translate = request.translate
    workbook = Workbook(file, {'default_date_format': 'dd.mm.yyyy'})

    agencies = workbook.add_worksheet(translate(_("Agencies")))
    agencies.write(0, 0, translate(_("ID")))
    agencies.write(0, 1, translate(_("Suborganizations")))
    agencies.write(0, 2, translate(_("Title")))
    agencies.write(0, 3, translate(_("Portrait")))
    agencies.write(0, 4, translate(_("Export Fields")))

    organigrams = workbook.add_worksheet(translate(_("Organigrams")))
    organigrams.write(0, 0, translate(_("Agency")))
    organigrams.write(0, 1, translate(_("Organigram")))

    o_row = 0
    for index, agency in enumerate(ExtendedAgencyCollection(session).query()):
        row = index + 1
        agencies.write(row, 0, str(agency.id))
        agencies.write(row, 1, ', '.join([str(c.id) for c in agency.children]))
        agencies.write(row, 2, agency.title)
        agencies.write(row, 3, agency.portrait)
        agencies.write(row, 4, ', '.join(agency.export_fields))

        if agency.organigram:
            o_row += 1
            organigrams.write(o_row, 0, str(agency.id))
            organigrams.insert_image(
                o_row, 1,
                agency.name,
                {'image_data': BytesIO(agency.organigram_file.read())}
            )
            organigrams.set_row(
                o_row,
                int(agency.organigram.reference.size[1].replace('px', ''))
            )

    people = workbook.add_worksheet(translate(_("People")))
    people.write(0, 0, translate(_("ID")))
    people.write(0, 1, translate(_("Salutation")))
    people.write(0, 2, translate(_("Academic Title")))
    people.write(0, 3, translate(_("First name")))
    people.write(0, 4, translate(_("Last name")))
    people.write(0, 5, translate(_("Profession")))
    people.write(0, 6, translate(_("Political Party")))
    people.write(0, 7, translate(_("Born")))
    people.write(0, 8, translate(_("Address")))
    people.write(0, 9, translate(_("Phone")))
    people.write(0, 10, translate(_("Direct Phone")))
    people.write(0, 11, translate(_("Email")))
    people.write(0, 12, translate(_("Website")))
    people.write(0, 13, translate(_("Notes")))

    memberships = workbook.add_worksheet(translate(_("Memberships")))
    memberships.write(0, 0, translate(_("Agency")))
    memberships.write(0, 1, translate(_("Person")))
    memberships.write(0, 2, translate(_("Title")))
    memberships.write(0, 3, translate(_("Since")))
    memberships.write(0, 4, translate(_("Prefix")))
    memberships.write(0, 5, translate(_("Addition")))
    memberships.write(0, 6, translate(_("Note")))

    m_row = 0
    for index, person in enumerate(ExtendedPersonCollection(session).query()):
        row = index + 1
        people.write(row, 0, str(index))
        people.write(row, 1, person.salutation)
        people.write(row, 2, person.academic_title)
        people.write(row, 3, person.first_name)
        people.write(row, 4, person.last_name)
        people.write(row, 5, person.profession)
        people.write(row, 6, person.political_party)
        people.write(row, 7, person.born)
        people.write(row, 8, person.address)
        people.write(row, 9, person.phone)
        people.write(row, 10, person.phone_direct)
        people.write(row, 11, person.email)
        people.write(row, 12, person.website)
        people.write(row, 13, person.notes)

        for membership in person.memberships:
            m_row += 1
            memberships.write(m_row, 0, str(membership.agency.id))
            memberships.write(m_row, 1, str(index))
            memberships.write(m_row, 2, membership.title)
            memberships.write(m_row, 3, membership.since)
            memberships.write(m_row, 4, membership.prefix)
            memberships.write(m_row, 5, membership.addition)
            memberships.write(m_row, 6, membership.note)

    workbook.close()


def import_from_xlsx():
    pass
