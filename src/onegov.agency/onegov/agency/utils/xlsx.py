from io import BytesIO
from onegov.agency import _
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedAgencyMembership
from onegov.agency.models import ExtendedPerson
from onegov.people import AgencyOrganigram
from xlsxwriter.workbook import Workbook


def export_to_xlsx(request, file):
    session = request.session
    translate = request.translate
    workbook = Workbook(file, {'default_date_format': 'dd.mm.yyyy'})

    # Agencies
    query = session.query(
        ExtendedAgency.id.label('id'),
        ExtendedAgency.parent_id.label('parent_id'),
        ExtendedAgency.title.label('title'),
        ExtendedAgency.portrait.label('portrait'),
        ExtendedAgency.meta['export_fields'].label('export_fields'),
    )
    query = query.order_by(ExtendedAgency.title)
    query = list(enumerate(query.all(), start=1))
    a_ids = {agency.id: str(a_id) for a_id, agency in query}

    sheet = workbook.add_worksheet(translate(_("Agencies")))
    sheet.write(0, 0, translate(_("ID")))
    sheet.write(0, 1, translate(_("Title")))
    sheet.write(0, 2, translate(_("Portrait")))
    sheet.write(0, 3, translate(_("Export Fields")))
    sheet.write(0, 4, translate(_("ID of Parent Organization")))
    for row, agency in query:
        sheet.write(row, 0, a_ids.get(agency.id))
        sheet.write(row, 1, agency.title)
        sheet.write(row, 2, agency.portrait)
        sheet.write(row, 3, ', '.join(agency.export_fields))
        sheet.write(row, 4, a_ids.get(agency.parent_id))

    # Organigrams
    sheet = workbook.add_worksheet(translate(_("Organigrams")))
    sheet.write(0, 0, translate(_("Agency")))
    sheet.write(0, 1, translate(_("Agency ID")))
    sheet.write(0, 2, translate(_("Organigram")))
    for row, organigram in enumerate(session.query(AgencyOrganigram), start=1):
        agency = organigram.linked_agencies[0]
        sheet.write(row, 0, agency.title)
        sheet.write(row, 1, a_ids.get(agency.id))
        sheet.insert_image(
            row, 2,
            organigram.reference.filename,
            {'image_data': BytesIO(organigram.reference.file.read())}
        )
        sheet.set_row(row, int(organigram.reference.size[1].replace('px', '')))

    # People
    query = session.query(
        ExtendedPerson.id.label('id'),
        ExtendedPerson.salutation.label('salutation'),
        ExtendedPerson.academic_title.label('academic_title'),
        ExtendedPerson.first_name.label('first_name'),
        ExtendedPerson.last_name.label('last_name'),
        ExtendedPerson.profession.label('profession'),
        ExtendedPerson.political_party.label('political_party'),
        ExtendedPerson.born.label('born'),
        ExtendedPerson.address.label('address'),
        ExtendedPerson.phone.label('phone'),
        ExtendedPerson.phone_direct.label('phone_direct'),
        ExtendedPerson.email.label('email'),
        ExtendedPerson.website.label('website'),
        ExtendedPerson.notes.label('notes'),
    )
    query = query.order_by(
        ExtendedPerson.last_name,
        ExtendedPerson.first_name
    )
    query = list(enumerate(query.all(), start=1))
    p_ids = {person.id: str(p_id) for p_id, person in query}

    sheet = workbook.add_worksheet(translate(_("People")))
    sheet.write(0, 0, translate(_("ID")))
    sheet.write(0, 1, translate(_("Salutation")))
    sheet.write(0, 2, translate(_("Academic Title")))
    sheet.write(0, 3, translate(_("First name")))
    sheet.write(0, 4, translate(_("Last name")))
    sheet.write(0, 5, translate(_("Profession")))
    sheet.write(0, 6, translate(_("Political Party")))
    sheet.write(0, 7, translate(_("Born")))
    sheet.write(0, 8, translate(_("Address")))
    sheet.write(0, 9, translate(_("Phone")))
    sheet.write(0, 10, translate(_("Direct Phone")))
    sheet.write(0, 11, translate(_("Email")))
    sheet.write(0, 12, translate(_("Website")))
    sheet.write(0, 13, translate(_("Notes")))
    for row, person in query:
        sheet.write(row, 0, p_ids.get(person.id))
        sheet.write(row, 1, person.salutation)
        sheet.write(row, 2, person.academic_title)
        sheet.write(row, 3, person.first_name)
        sheet.write(row, 4, person.last_name)
        sheet.write(row, 5, person.profession)
        sheet.write(row, 6, person.political_party)
        sheet.write(row, 7, person.born)
        sheet.write(row, 8, person.address)
        sheet.write(row, 9, person.phone)
        sheet.write(row, 10, person.phone_direct)
        sheet.write(row, 11, person.email)
        sheet.write(row, 12, person.website)
        sheet.write(row, 13, person.notes)

    # Memberships
    query = session.query(
        ExtendedAgencyMembership.agency_id.label('agency_id'),
        ExtendedAgencyMembership.person_id.label('person_id'),
        ExtendedAgencyMembership.title.label('title'),
        ExtendedAgencyMembership.since.label('since'),
        ExtendedAgencyMembership.meta['prefix'].astext.label('prefix'),
        ExtendedAgencyMembership.meta['addition'].astext.label('addition'),
        ExtendedAgencyMembership.meta['note'].astext.label('note'),
        ExtendedAgencyMembership.order.label('order'),
    )
    query = list(enumerate(query.all(), start=1))

    sheet = workbook.add_worksheet(translate(_("Memberships")))
    sheet.write(0, 0, translate(_("Agency")))
    sheet.write(0, 1, translate(_("Person")))
    sheet.write(0, 2, translate(_("Title")))
    sheet.write(0, 3, translate(_("Since")))
    sheet.write(0, 4, translate(_("Prefix")))
    sheet.write(0, 5, translate(_("Addition")))
    sheet.write(0, 6, translate(_("Note")))
    sheet.write(0, 7, translate(_("Order")))
    for row, membership in query:
        sheet.write(row, 0, a_ids.get(membership.agency_id))
        sheet.write(row, 1, p_ids.get(membership.person_id))
        sheet.write(row, 2, membership.title)
        sheet.write(row, 3, membership.since)
        sheet.write(row, 4, membership.prefix)
        sheet.write(row, 5, membership.addition)
        sheet.write(row, 6, membership.note)
        sheet.write(row, 7, str(membership.order))

    workbook.close()


def import_from_xlsx():
    pass
