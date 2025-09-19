from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from onegov.pas import log
from onegov.pas.models import (
    PASCommission,
    PASCommissionMembership,
    PASParliamentarian,
    PASParliamentarianRole,
    PASParliamentaryGroup,
    Party,
)
from sqlalchemy.orm import selectinload


from typing import Any, Literal, TypedDict


# Define TypedDicts for data structures used in JSON import
# These are defined outside TYPE_CHECKING to be available at runtime
# Because we validate the json structure has actually these fields
class OrganizationData(TypedDict):
    created: str
    description: str
    htmlUrl: str
    id: str
    isActive: bool
    memberCount: int
    modified: str
    name: str
    organizationTypeTitle: (
        Literal['Kommission', 'Fraktion', 'Kantonsrat', 'Sonstige'] | None
    )
    primaryEmail: None
    status: int
    thirdPartyId: str | None
    url: str


class EmailData(TypedDict):
    id: str
    label: str
    email: str
    isDefault: bool
    thirdPartyId: str | None
    modified: str
    created: str


class AddressData(TypedDict):
    formattedAddress: str
    id: str
    label: str
    isDefault: bool
    organisationName: str
    organisationNameAddOn1: str
    organisationNameAddOn2: str
    addressLine1: str
    addressLine2: str
    street: str
    houseNumber: str
    dwellingNumber: str
    postOfficeBox: str
    swissZipCode: str
    swissZipCodeAddOn: str
    swissZipCodeId: str
    foreignZipCode: str
    locality: str
    town: str
    countryIdISO2: str
    countryName: str
    thirdPartyId: str | None
    modified: str
    created: str


class PhoneNumberData(TypedDict):
    id: str
    label: str
    phoneNumber: str
    phoneCategory: int
    otherPhoneCategory: str | None
    phoneCategoryText: str
    isDefault: bool
    thirdPartyId: str | None
    modified: str
    created: str


class UrlData(TypedDict):
    id: str
    label: str
    url: str | None
    isDefault: bool
    thirdPartyId: str | None
    modified: str
    created: str


class OrganizationDataWithinMembership(TypedDict):
    created: str
    description: str
    htmlUrl: str
    id: str
    isActive: bool
    memberCount: int
    modified: str
    name: str
    organizationTypeTitle: (
        Literal['Kommission', 'Fraktion', 'Kantonsrat', 'Sonstige'] | None
    )
    primaryEmail: EmailData | None
    status: int
    thirdPartyId: str | None
    url: str
    organizationType: int
    primaryAddress: AddressData | None
    primaryPhoneNumber: PhoneNumberData | None
    primaryUrl: UrlData | None
    statusDisplay: str
    tags: list[str]
    type: str


class PersonData(TypedDict):
    created: str
    firstName: str
    fullName: str
    htmlUrl: str
    id: str
    isActive: bool
    modified: str
    officialName: str
    personTypeTitle: str | None
    primaryEmail: EmailData | None
    salutation: str
    tags: list[str]
    thirdPartyId: str
    title: str
    url: str
    username: str | None


class MembershipData(TypedDict):
    department: str
    description: str
    emailReceptionType: str
    end: str | bool | None
    id: str
    isDefault: bool
    organization: OrganizationDataWithinMembership
    person: PersonData
    primaryAddress: AddressData | None
    primaryEmail: EmailData | None
    primaryPhoneNumber: PhoneNumberData | None
    primaryUrl: UrlData | None
    email: EmailData | None
    phoneNumber: PhoneNumberData | None
    address: AddressData | None
    urlField: UrlData | None
    role: str
    start: str | bool | None
    text: str
    thirdPartyId: str | None
    type: str
    typedId: str
    url: str


from typing import TYPE_CHECKING, TypedDict
if TYPE_CHECKING:
    from onegov.parliament.models.parliamentarian_role import (
        ParliamentaryGroupRole, PartyRole, Role)
    from collections.abc import Sequence
    from sqlalchemy.orm import Session

    class ImportCategoryResult(TypedDict):
        created: list[Any]
        updated: list[Any]
        processed: int


class DataImporter:
    """Base class for all importers with common functionality."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def parse_date(
        self,
        date_string: str | None,
    ) -> date | None:
        if not date_string:
            return None
        try:
            # Handle potential timezone info if present
            if date_string.endswith('Z'):
                date_string = date_string[:-1] + '+00:00'
            dt = datetime.fromisoformat(date_string)
            return dt.date()
        except ValueError:
            log.warning(f'Could not parse date string: {date_string}')
            return None

    def _bulk_save(self, objects: list[Any], object_type: str) -> int:
        """Save a batch of objects to the database and return the count."""
        count = 0
        try:
            if objects:
                count = len(objects)
                self.session.add_all(objects)
                # Flush is removed, commit at the end of import_zug_kub_data
                log.info(f'Saved {count} new {object_type}')
            return count
        except Exception as e:
            log.error(
                f'Error saving {count} {object_type}: {e}', exc_info=True
            )
            self.session.rollback()
            raise RuntimeError(f'Error bulk saving {object_type}') from e


class PeopleImporter(DataImporter):
    """Importer for Parliamentarian data from api/v2/people endpoint
        (People.json)


    API Inconsistency Note:
    The API design is inconsistent regarding address information.
    While 'people.json', which is expected to be the primary source
    for person details, *lacks* address information, 'memberships.json'
    *does* embed address data within the 'person' object and sometimes
    at the membership level. This requires us to extract address data
    from 'memberships.json' instead of the more logical 'people.json'
    endpoint.

    Whatever the reasons for this, we need to be careful to avoid potential
    inconsistencies if addresses are not carefully managed across both
    endpoints in the source system

    """

    person_attribute_map: dict[str, str] = {
        'id': 'external_kub_id',
        'firstName': 'first_name',
        'officialName': 'last_name',
        'title': 'academic_title',
        'salutation': 'salutation',
    }

    def bulk_import(self, people_data: Sequence[PersonData]) -> tuple[
        dict[str, PASParliamentarian],
        dict[str, list[PASParliamentarian]],
        int,  # Add processed count
    ]:
        """
        Imports people from JSON data.

        Returns:
            A tuple containing:
            - A map of external KUB ID to Parliamentarian objects.
            - A dictionary with lists of created and updated parliamentarians.
            - The total number of people records processed from the input.
        """
        new_parliamentarians: list[PASParliamentarian] = []
        updated_parliamentarians: list[PASParliamentarian] = []
        processed_count = 0
        result_map: dict[str, PASParliamentarian] = {}

        # Fetch existing parliamentarians by external_kub_id
        existing_ids = [p['id'] for p in people_data if p.get('id')]
        existing_parliamentarians = (
            self.session.query(PASParliamentarian)
            .filter(PASParliamentarian.external_kub_id.in_(existing_ids))
            .all()
        )
        existing_map = {
            p.external_kub_id: p
            for p in existing_parliamentarians
            if p.external_kub_id
        }

        for person_data in people_data:
            processed_count += 1  # Count each record we attempt to process
            person_id = person_data.get('id')
            if not person_id:
                log.warning(
                    f'Skipping person entry due to missing ID: '
                    f'{person_data.get("fullName")}'
                )
                continue

            try:
                # Check if this person ID has already been processed in this
                # batch
                if person_id in result_map:
                    log.warning(
                        f'Skipping duplicate person ID within import batch: '
                        f'{person_id}'
                    )
                    continue

                # Convert person_id string to UUID for DB lookup
                try:
                    person_uuid = UUID(person_id)
                except ValueError:
                    log.exception(
                        f'Skipping person due to invalid UUID format: '
                        f'{person_id} - {person_data.get("fullName")}'
                    )
                    continue

                parliamentarian = existing_map.get(person_uuid)

                if parliamentarian:
                    # Update existing parliamentarian from DB
                    was_updated = self._update_parliamentarian_attributes(
                        parliamentarian, person_data
                    )
                    log.debug(
                        f'Updating existing parliamentarian: {person_id}'
                    )
                    if was_updated:
                        updated_parliamentarians.append(parliamentarian)
                    result_map[person_id] = parliamentarian
                else:
                    parliamentarian = self._create_parliamentarian(person_data)
                    if not parliamentarian:
                        continue
                    log.debug(f'Creating new parliamentarian: {person_id}')
                    new_parliamentarians.append(parliamentarian)
                    result_map[person_id] = parliamentarian
                    # Add to new list, _bulk_save confirms DB insert
            except Exception as e:
                log.error(
                    f'Error processing person with id {person_id}: {e}',
                    exc_info=True,
                )

        # Log individual details of new parliamentarians
        if new_parliamentarians:
            emails_or_names = []
            for p in new_parliamentarians:
                identifier = p.email_primary or (
                    f'{p.first_name} {p.last_name}'.strip()
                )
                if identifier:
                    emails_or_names.append(identifier)

            if emails_or_names:
                log.info(
                    'New parliamentarians '
                    f'created: {", ".join(emails_or_names)}'
                )

        self._bulk_save(new_parliamentarians, 'new parliamentarians')

        # Filter out any objects that failed to save
        # (though _bulk_save raises on DB error)
        created_list = [p for p in new_parliamentarians if p.id]
        updated_list = [p for p in updated_parliamentarians if p.id]

        details = {'created': created_list, 'updated': updated_list}
        log.info(
            f'Parliamentarian import details: '
            f'Created: {len(details["created"])}, '
            f'Updated: {len(details["updated"])}, '
            f'Processed: {processed_count}'
        )
        return result_map, details, processed_count

    def _update_parliamentarian_attributes(
        self, parliamentarian: PASParliamentarian, person_data: PersonData
    ) -> bool:
        """Updates attributes of an existing Parliamentarian object.
        Returns True if any attributes were changed, False otherwise."""
        changed = False
        for json_key, model_attr in self.person_attribute_map.items():
            if val := person_data.get(json_key):
                # Only update if the value is different to avoid unnecessary
                # writes
                if getattr(parliamentarian, model_attr) != val:
                    setattr(parliamentarian, model_attr, val)
                    changed = True

        # Handle nested primaryEmail
        primary_email_data = person_data.get('primaryEmail')
        new_email = (
            primary_email_data.get('email') if primary_email_data else None
        )
        if new_email and parliamentarian.email_primary != new_email:
            parliamentarian.email_primary = new_email
            changed = True

        return changed

    def _create_parliamentarian(
        self, person_data: PersonData
    ) -> PASParliamentarian | None:
        """Creates a single new Parliamentarian object from person data."""

        person_id = person_data.get('id')
        person_id = person_data.get('id')
        if not person_id:
            log.error(
                f'Skipping person creation due to missing ID: '
                f'{person_data.get("fullName")}'
            )
            return None

        parliamentarian_kwargs = {}
        for json_key, model_attr in self.person_attribute_map.items():
            if val := person_data.get(json_key):
                parliamentarian_kwargs[model_attr] = val

        # Handle nested primaryEmail
        primary_email_data = person_data.get('primaryEmail')
        if primary_email_data and primary_email_data.get('email'):
            parliamentarian_kwargs['email_primary'] = primary_email_data[
                'email'
            ]

        parliamentarian = PASParliamentarian(**parliamentarian_kwargs)
        return parliamentarian


class OrganizationImporter(DataImporter):
    """Importer for organization data from organizations.json."""

    def bulk_import(
        self, organizations_data: Sequence[OrganizationData]
    ) -> tuple[
        dict[str, PASCommission],
        dict[str, PASParliamentaryGroup],  # Currently unused, but kept for
        # structure
        dict[str, Party],
        dict[str, Any],  # Other orgs
        dict[str, dict[str, list[PASCommission | Party]]],  # Details
        dict[str, int],  # Processed counts per type
    ]:
        """
        Imports organizations from JSON data. Returns maps, details, and
        counts.

        Returns:
            Tuple containing maps of external IDs to:
            - Commissions
            - Parliamentary Groups
            - Parties (created from parliamentary groups)
            - Other organizations
            - Dictionary containing lists of created/updated objects per type.
        """
        commissions_to_create: list[PASCommission] = []
        commissions_to_update: list[PASCommission] = []
        parties_to_create: list[Party] = []
        parties_to_update: list[Party] = []

        # Details structure to return
        details: dict[str, dict[str, list[PASCommission | Party]]] = {
            'commissions': {'created': [], 'updated': []},
            'parliamentary_groups': {'created': [], 'updated': []},
            'parties': {'created': [], 'updated': []},
            # 'other' are not ORM objects, just counted/listed
        }
        processed_counts = {
            'commissions': 0,
            'parliamentary_groups': 0,  # Fraktion
            'parties': 0,  # Also Fraktion, mapped to Party
            'other': 0,  # Kantonsrat, Sonstige, Legislatur
        }

        # Maps to return (will contain both existing and new objects)
        commission_map: dict[str, PASCommission] = {}
        parliamentary_group_map: dict[str, PASParliamentaryGroup] = {}
        party_map: dict[str, Party] = {}
        # Not ORM objects, no update needed
        other_organizations: dict[str, Any] = {}

        # Fetch existing organizations by external_kub_id
        existing_ids = [o['id'] for o in organizations_data if o.get('id')]
        existing_commissions = (
            self.session.query(PASCommission)
            .filter(PASCommission.external_kub_id.in_(existing_ids))
            .all()
        )
        existing_parties = (
            self.session.query(Party)
            .filter(Party.external_kub_id.in_(existing_ids))
            .all()
        )

        existing_commission_map = {
            c.external_kub_id: c for c in existing_commissions
        }
        existing_party_map = {p.external_kub_id: p for p in existing_parties}

        for org_data in organizations_data:
            org_id = org_data.get('id')
            if not org_id:
                log.warning(  # Downgrade to warning
                    f'Skipping organization without ID: {org_data.get("name")}'
                )
                continue

            organization_type_title = org_data.get('organizationTypeTitle')
            org_name = org_data.get('name')

            try:
                organization_type_title = org_data.get('organizationTypeTitle')
                org_name = org_data.get('name', '')

                if organization_type_title == 'Kommission':
                    processed_counts['commissions'] += 1
                    try:
                        org_uuid = UUID(org_id)
                    except ValueError:
                        log.exception(
                            f'Invalid UUID for commission ID: {org_id}'
                        )
                        continue

                    commission = existing_commission_map.get(org_uuid)
                    if commission:
                        # Update existing commission found in initial query
                        updated = False
                        if commission.name != org_name:
                            commission.name = org_name
                            updated = True
                        if updated:
                            commissions_to_update.append(commission)
                            log.debug(
                                f'Updating commission (from initial query): '
                                f'{org_id}'
                            )
                        # No need to add to save list, session tracks changes
                    else:
                        commission = PASCommission(
                            external_kub_id=org_uuid,
                            name=org_name,
                            type='normal',
                        )
                        log.debug(f'Creating new commission: {org_id}')
                        # Only add *new* commissions to the save list
                        commissions_to_create.append(commission)

                    # Add to map regardless
                    commission_map[org_id] = commission

                elif organization_type_title == 'Fraktion':
                    # Count both as parliamentary_group and party for
                    # processing
                    processed_counts['parliamentary_groups'] += 1
                    processed_counts['parties'] += 1
                    try:
                        org_uuid = UUID(org_id)
                    except ValueError:
                        log.exception(
                            f'Invalid UUID for party/Fraktion ID: {org_id}'
                        )
                        continue

                    # Treat 'Fraktion' as Party based on observation
                    party = existing_party_map.get(org_uuid)
                    if party:
                        # Update existing party found in initial query
                        updated = False
                        if party.name != org_name:
                            party.name = org_name
                            updated = True
                        if updated:
                            parties_to_update.append(party)
                            log.debug(
                                f'Updating party (from Fraktion, initial '
                                f'query): {org_id}'
                            )
                        # No need to add to save list, session tracks changes
                    else:
                        # Create new party (since not found in initial map)
                        party = (
                            Party(external_kub_id=org_uuid, name=org_name))
                        log.debug(
                            f'Creating party (from Fraktion): {org_id}'
                        )
                        # Only add *new* parties to the save list
                        parties_to_create.append(party)

                    # Use org_id for party_map key consistency
                    party_map[org_id] = party

                elif organization_type_title in ('Kantonsrat', 'Sonstige'):
                    processed_counts['other'] += 1
                    other_organizations[org_id] = {
                        'id': org_id,
                        'name': org_data.get('name', ''),
                        'type': organization_type_title.lower(),
                    }
                elif org_name is not None and 'Legislatur' in org_name:
                    # Count Legislatur as 'other'
                    processed_counts['other'] += 1
                else:
                    # Count unknown types as 'other' as well
                    processed_counts['other'] += 1
                    log.warning(
                        f'Unknown organization type: {organization_type_title}'
                        f' for {org_name}'
                    )

            except Exception as e:
                log.error(
                    f'Error importing organization '
                    f'{org_data.get("name")}: {e}',
                    exc_info=True,
                )

        # Save newly created objects
        if commissions_to_create:
            self._bulk_save(commissions_to_create, 'new commissions')
        # if parliamentary_groups_to_create: # Not implemented
        #     self._bulk_save(parliamentary_groups_to_create,
        #                     'new parliamentary groups')
        if parties_to_create:
            self._bulk_save(parties_to_create, 'new parties')

        # Flush is removed, commit at the end of import_zug_kub_data
        # IDs will be assigned after the final commit.

        details['commissions']['created'] = list(commissions_to_create)
        details['commissions']['updated'] = list(commissions_to_update)
        details['parties']['created'] = list(parties_to_create)
        details['parties']['updated'] = list(parties_to_update)
        log.info(
            f'Organization import details: '
            f'Commissions(C:{len(details["commissions"]["created"])}, '
            f'U:{len(details["commissions"]["updated"])}, '
            f'P:{processed_counts["commissions"]}), '
            f'Parties(C:{len(details["parties"]["created"])}, '
            f'U:{len(details["parties"]["updated"])}, '
            f'P:{processed_counts["parties"]}), '  # Note: Parties from Frakt.
            f'Other Processed: {processed_counts["other"]}'
        )

        # Return maps, details, and processed counts
        return (
            commission_map,
            parliamentary_group_map,
            party_map,
            other_organizations,
            details,
            processed_counts,  # Add processed counts here
        )


class MembershipImporter(DataImporter):
    """Importer for membership data from memberships.json.

    Get an overview of the possible pairs: see extract_role_org_type_pairs:

    Role - Organization Type Combinations:
    =====================================
    Assistentin Leitung Staatskanzlei - Sonstige
    Frau Landammann - Sonstige
    Landammann - Sonstige
    Landschreiber - Sonstige
    Mitglied - Kommission
    Mitglied des Kantonsrates - Kantonsrat
    Nationalrat - Sonstige
    Parlamentarier - Sonstige
    Parlamentarierin - Sonstige
    Protokollführerin - Sonstige
    Präsident des Kantonsrates - Kantonsrat
    Präsident/-in - Kommission
    Regierungsrat - Sonstige
    Regierungsrätin - Sonstige
    Standesweibel - Sonstige
    Standesweibelin - Sonstige
    Statthalter - Sonstige
    Stv. Landschreiberin - Sonstige
    Stv. Protokollführer - Sonstige
    Stv. Protokollführerin - Sonstige
    Stv. Standesweibelin - Sonstige
    Ständerat - Sonstige

    Total unique combinations: 22

    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.parliamentarian_map: dict[str, PASParliamentarian] = {}
        self.commission_map: dict[str, PASCommission] = {}
        self.parliamentary_group_map: dict[str, PASParliamentaryGroup] = {}
        # party_map now keyed by external_kub_id for consistency
        self.party_map: dict[str, Party] = {}
        self.other_organization_map: dict[str, Any] = {}

    def init(
        self,
        session: Session,
        parliamentarian_map: dict[str, PASParliamentarian],
        commission_map: dict[str, PASCommission],
        parliamentary_group_map: dict[str, PASParliamentaryGroup],
        party_map: dict[str, Party],
        other_organization_map: dict[str, Any],
    ) -> None:
        """Initialize the importer with maps of objects by their external KUB
        ID."""
        self.session = session
        self.parliamentarian_map = parliamentarian_map
        self.commission_map = commission_map
        self.parliamentary_group_map = parliamentary_group_map
        self.party_map = party_map
        self.other_organization_map = other_organization_map

    def _extract_and_update_or_create_missing_parliamentarians(
        self, memberships_data: Sequence[MembershipData]
    ) -> dict[str, list[PASParliamentarian]]:
        """
        Extracts/updates/creates parliamentarians found only in membership
        data.

        Returns a dictionary with lists of created and updated
        parliamentarians found during this process.

        If a parliamentarian is not already known (from people.json import),
        check if they exist in the DB. If yes, update them with potentially
        missing info (address, email) from membership data. If no, create a
        new parliamentarian. Updates self.parliamentarian_map accordingly.
        """
        parliamentarians_to_create: list[PASParliamentarian] = []
        # Use a set for updates to automatically handle duplicates
        parliamentarians_to_update: set[PASParliamentarian] = set()

        # 1. Identify potential missing parliamentarian IDs
        missing_person_ids = {
            m['person']['id']
            for m in memberships_data
            if m.get('person')
            and m['person'].get('id')
            and m['person']['id'] not in self.parliamentarian_map
        }

        if not missing_person_ids:
            log.debug(
                'No missing parliamentarians found only in membership data.'
            )
            return {'created': [], 'updated': []}

        existing_db_parliamentarians = (
            self.session.query(PASParliamentarian)
            .filter(PASParliamentarian.external_kub_id.in_(missing_person_ids))
            .all()
        )
        existing_db_map = {
            p.external_kub_id: p for p in existing_db_parliamentarians
        }
        log.debug(
            f'Found {len(existing_db_map)} existing parliamentarians in DB '
            f'matching missing IDs.'
        )

        for membership in memberships_data:
            person_data = membership.get('person')
            person_id = None  # Initialize person_id
            try:
                if not person_data:
                    continue
                person_id = person_data.get('id')
                if not person_id or person_id in self.parliamentarian_map:
                    continue
                try:
                    person_uuid = UUID(person_id)
                    existing_parliamentarian = existing_db_map.get(person_uuid)
                except ValueError:
                    log.warning(
                        f'Invalid UUID format for person ID: {person_id}'
                    )
                    existing_parliamentarian = None

                if existing_parliamentarian:
                    # Update existing DB parliamentarian if needed
                    updated = self._update_parliamentarian_from_membership(
                        existing_parliamentarian, person_data, membership
                    )
                    if updated:
                        # Add to set; duplicates are automatically handled
                        parliamentarians_to_update.add(
                            existing_parliamentarian
                        )
                        log.info(
                            f'Updated existing parliamentarian '
                            f'(ID: {person_id}) found via membership data.'
                        )
                    # Add to map whether updated or not
                    self.parliamentarian_map[person_id] = (
                        existing_parliamentarian
                    )

                else:
                    # Create new parliamentarian
                    full_name = person_data.get('fullName', 'N/A')
                    log.info(
                        f'Creating new parliamentarian (ID: {person_id}) '
                        f'found only in membership data: {full_name}'
                    )
                    new_parliamentarian = (
                        self._create_parliamentarian_from_membership(
                            person_data, membership
                        )
                    )
                    if new_parliamentarian:
                        parliamentarians_to_create.append(new_parliamentarian)
                        self.parliamentarian_map[person_id] = (
                            new_parliamentarian
                        )

            except Exception as e:
                # Use the initialized person_id here
                log_person_id = person_id if person_id else 'unknown'
                log.error(
                    f'Error processing potential missing parliamentarian from '
                    f'membership (Person ID: {log_person_id}): {e}',
                    exc_info=True,
                )

        # Save new parliamentarians
        if parliamentarians_to_create:
            self._bulk_save(
                parliamentarians_to_create,
                'new parliamentarians from memberships',
            )

        # Flush is removed, commit at the end of import_zug_kub_data
        # IDs will be assigned after the final commit.
        try:
            # We still need to add the newly created objects to the session
            # if _bulk_save didn't run (list was empty)
            if parliamentarians_to_create:
                self.session.add_all(parliamentarians_to_create)

            created_count = len(parliamentarians_to_create)
            updated_count = len(parliamentarians_to_update)
            log.info(
                f'Created {created_count} and updated {updated_count} '
                f'parliamentarians based *only* on membership data.'
            )
            # Update map with newly created objects (now with IDs)
            for p in parliamentarians_to_create:
                if p.external_kub_id:  # Should have ID after flush
                    # Map using external ID before commit assigns internal ID
                    self.parliamentarian_map[str(p.external_kub_id)] = p

            # Filter lists based on object existence, not internal ID yet
            created_list = list(parliamentarians_to_create)
            # Convert set to list for the return value
            updated_list = list(parliamentarians_to_update)

        except Exception:
            log.error(
                'Error flushing parliamentarians from membership data',
                exc_info=True,
            )
            self.session.rollback()
            # Return empty lists on error
            created_list = []
            updated_list = []

        details = {'created': created_list, 'updated': updated_list}
        return details

    def _update_parliamentarian_from_membership(
        self,
        parliamentarian: PASParliamentarian,
        person_data: PersonData,
        membership_data: MembershipData,
    ) -> bool:
        """
        Updates an existing parliamentarian with info from membership data,
        focusing on potentially missing fields like email and address.
        Returns True if any changes were made, False otherwise.
        """
        changed = False

        # Update basic info if missing
        if not parliamentarian.first_name and person_data.get('firstName'):
            parliamentarian.first_name = person_data['firstName']
            changed = True
        if not parliamentarian.last_name and person_data.get('officialName'):
            parliamentarian.last_name = person_data['officialName']
            changed = True
        if not parliamentarian.salutation and person_data.get('salutation'):
            parliamentarian.salutation = person_data['salutation']
            changed = True
        if not parliamentarian.academic_title and person_data.get('title'):
            parliamentarian.academic_title = person_data['title']
            changed = True

        # Update email if missing or different
        primary_email_data = person_data.get('primaryEmail')
        new_email = (
            primary_email_data.get('email') if primary_email_data else None
        )
        if new_email and parliamentarian.email_primary != new_email:
            parliamentarian.email_primary = new_email
            changed = True

        # Update address if missing or different
        address_data = membership_data.get('primaryAddress')
        if address_data:
            street = address_data.get('street', '')
            house_num = address_data.get('houseNumber', '')
            new_address = f'{street} {house_num}'.strip()
            new_zip = address_data.get('swissZipCode')
            new_city = address_data.get('town')

            if new_address and parliamentarian.shipping_address != new_address:
                parliamentarian.shipping_address = new_address
                changed = True
            if (
                new_zip
                and parliamentarian.shipping_address_zip_code != new_zip
            ):
                parliamentarian.shipping_address_zip_code = new_zip
                changed = True
            if new_city and parliamentarian.shipping_address_city != new_city:
                parliamentarian.shipping_address_city = new_city
                changed = True

        return changed

    def _create_parliamentarian_from_membership(
        self, person_data: PersonData, membership_data: MembershipData
    ) -> PASParliamentarian | None:
        """
        Creates a new Parliamentarian object using data primarily from a
        membership record.
        """
        person_id = person_data.get('id')
        if not person_id:
            log.error(
                'Cannot create parliamentarian from membership: '
                'Missing person ID.'
            )
            return None

        try:
            uuid_value = UUID(person_id)
            parliamentarian = PASParliamentarian(
                external_kub_id=uuid_value,
                first_name=person_data.get('firstName', ''),
                last_name=person_data.get('officialName', ''),
                salutation=person_data.get('salutation'),
                academic_title=person_data.get('title'),
            )

            # Handle email
            primary_email_data = person_data.get('primaryEmail')
            if primary_email_data and primary_email_data.get('email'):
                parliamentarian.email_primary = primary_email_data['email']

            # Handle address
            address_data = membership_data.get('primaryAddress')
            if address_data:
                street = address_data.get('street', '')
                house_num = address_data.get('houseNumber', '')
                parliamentarian.shipping_address = (
                    f'{street} {house_num}'.strip()
                )
                parliamentarian.shipping_address_zip_code = address_data.get(
                    'swissZipCode'
                )
                parliamentarian.shipping_address_city = address_data.get(
                    'town'
                )

            return parliamentarian
        except Exception as e:
            log.error(
                f'Error creating parliamentarian from membership data '
                f'(Person ID: {person_id}): {e}',
                exc_info=True,
            )
            return None

    def bulk_import(
        self, memberships_data: Sequence[MembershipData]
    ) -> tuple[
        dict[str, ImportCategoryResult | dict[str, list[Any]]], dict[str, int]
    ]:
        """
        Imports memberships from JSON data based on organization type.

        Returns:
            - A dictionary containing lists of created/updated objects and
              processed counts per category.
            - A dictionary containing the count of processed items per type.
        """
        commission_memberships_to_create: list[PASCommissionMembership] = []
        commission_memberships_to_update: list[PASCommissionMembership] = []
        parliamentarian_roles_to_create: list[PASParliamentarianRole] = []
        parliamentarian_roles_to_update: list[PASParliamentarianRole] = []

        # Details structure to return - Use the new TypedDict where applicable
        details: dict[str, ImportCategoryResult | dict[str, Any]] = {
            'parliamentarians_from_memberships': {
                'created': [],
                'updated': [],
            },
            'commission_memberships': {
                'created': [],
                'updated': [],
                'processed': 0,
            },
            'parliamentarian_roles': {
                'created': [],
                'updated': [],
                'processed': 0,
            },
        }
        processed_counts = {
            'commission_memberships': 0,
            'parliamentarian_roles': 0,  # Covers Fraktion, Kantonsrat,
            # Sonstige
            'skipped': 0,  # Count memberships we couldn't process
        }

        # Process parliamentarians found only in memberships first
        parl_details = (
            self._extract_and_update_or_create_missing_parliamentarians(
                memberships_data
            )
        )
        details['parliamentarians_from_memberships']['created'] = parl_details[
            'created'
        ]
        details['parliamentarians_from_memberships']['updated'] = parl_details[
            'updated'
        ]

        # --- Pre-fetch existing memberships and roles ---
        parliamentarian_ids = [
            p.id for p in self.parliamentarian_map.values() if p.id
        ]
        commission_ids = [c.id for c in self.commission_map.values() if c.id]
        [p.id for p in self.party_map.values() if p.id]
        [g.id for g in self.parliamentary_group_map.values() if g.id]

        existing_commission_memberships_map: dict[
            tuple[UUID | None, UUID | None], PASCommissionMembership
        ] = {}
        if parliamentarian_ids and commission_ids:
            existing_cms = (
                self.session.query(PASCommissionMembership)
                .filter(
                    PASCommissionMembership.parliamentarian_id.in_(
                        parliamentarian_ids
                    ),
                    PASCommissionMembership.commission_id.in_(commission_ids),
                )
                .all()
            )
            existing_commission_memberships_map = {
                (cm.parliamentarian_id, cm.commission_id): cm
                for cm in existing_cms
            }
            log.debug(
                f'Pre-fetched {len(existing_commission_memberships_map)} '
                f'existing commission memberships.'
            )

        # Define the precise structure for the role key tuple
        role_key_type = tuple[UUID, UUID | None, UUID | None, str, str | None]
        existing_roles_map: dict[role_key_type, PASParliamentarianRole] = {}
        if parliamentarian_ids:
            # Fetch all roles for the relevant parliamentarians
            # We'll filter/map them client-side
            existing_roles = (
                self.session.query(PASParliamentarianRole)
                .filter(
                    PASParliamentarianRole.parliamentarian_id.in_(
                        parliamentarian_ids
                    )
                )
                .options(
                    # Eager load related objects to prevent N+1 queries
                    # during updates.
                    selectinload(PASParliamentarianRole.party),
                    selectinload(PASParliamentarianRole.parliamentary_group),
                )
                .all()
            )
            for role_obj in existing_roles:
                # Create a unique key based on the role type and relevant IDs
                # Use the defined role_key_type hint for clarity
                if role_obj.party_id or role_obj.parliamentary_group_id:
                    # Fraktion/Party Role (assuming role='member')
                    current_role_key = (
                        role_obj.parliamentarian_id,
                        role_obj.party_id,
                        role_obj.parliamentary_group_id,
                        'member',  # Explicitly add role type for uniqueness
                        None,  # Placeholder for additional_information
                    )
                elif role_obj.additional_information:
                    # Sonstige Role (assuming role='member')
                    current_role_key = (
                        role_obj.parliamentarian_id,
                        None,  # party_id
                        None,  # group_id
                        'member',  # Explicitly add role type
                        role_obj.additional_information,
                    )
                else:
                    # Kantonsrat Role (or potentially others without
                    # party/group/add.info)
                    current_role_key = (
                        role_obj.parliamentarian_id,
                        None,  # party_id
                        None,  # group_id
                        role_obj.role,  # Use the actual role
                        None,  # Placeholder for additional_information
                    )
                existing_roles_map[current_role_key] = role_obj
            log.debug(
                f'Pre-fetched {len(existing_roles_map)} existing '
                f'parliamentarian roles.'
            )
        # --- End Pre-fetching ---

        for membership in memberships_data:
            person_id = None
            processed_membership_type = False  # Flag to track if counted
            try:
                # Safely access nested keys
                person_data = membership.get('person')
                if not person_data:
                    log.warning(
                        'Skipping membership: Missing person data.'
                    )
                    continue
                person_id = person_data.get('id')
                if not person_id:
                    log.warning(
                        'Skipping membership: Missing person ID in data.'
                    )
                    continue

                org_data = membership.get('organization')
                if not org_data:
                    log.warning(
                        f'Skipping membership for person {person_id}: '
                        f'Missing organization data.'
                    )
                    continue
                org_id = org_data.get('id')
                if not org_id:
                    log.warning(
                        f'Skipping membership for person {person_id}: '
                        f'Missing organization ID.'
                    )
                    continue
                parliamentarian = self.parliamentarian_map.get(person_id)
                if not parliamentarian:
                    log.warning(
                        f'Skipping membership: Parliamentarian with external '
                        f'KUB ID {person_id} not found.'
                    )
                    continue

                org_type_title = org_data.get('organizationTypeTitle')
                role_text = membership.get('role', '')
                org_name = org_data.get('name', '')

                if org_type_title == 'Kommission':
                    processed_counts['commission_memberships'] += 1
                    processed_membership_type = True
                    commission = self.commission_map.get(org_id)
                    if not commission:
                        log.warning(
                            f'Skipping commission membership: Commission with '
                            f'external KUB ID {org_id} not found.'
                        )
                        continue

                    membership_key = (parliamentarian.id, commission.id)
                    existing_membership = (
                        existing_commission_memberships_map.get(membership_key)
                    )

                    if existing_membership:
                        # Update existing membership (changes tracked by
                        # session)
                        updated = self._update_commission_membership(
                            existing_membership, membership
                        )
                        if updated:
                            commission_memberships_to_update.append(
                                existing_membership
                            )
                            log.debug(
                                f'Updating commission membership for '
                                f'{parliamentarian.id} in {commission.id}'
                            )
                        # No need to append, session flush handles updates.
                    else:
                        # Create new membership
                        membership_obj = self._create_commission_membership(
                            parliamentarian, commission, membership
                        )
                        if membership_obj:
                            commission_memberships_to_create.append(
                                membership_obj
                            )
                            # Add the new membership to the map to prevent
                            # duplicates within the same import run if data is
                            # redundant
                            if parliamentarian.id and commission.id:
                                new_key = (parliamentarian.id, commission.id)
                                existing_commission_memberships_map[
                                    new_key
                                ] = membership_obj
                            log.debug(
                                f'Creating commission membership for '
                                f'{parliamentarian.id} in {commission.id}'
                            )

                elif org_type_title == 'Fraktion':
                    processed_counts['parliamentarian_roles'] += 1
                    processed_membership_type = True
                    party = self.party_map.get(org_id)
                    if not party:
                        log.warning(
                            f'Skipping Fraktion role: Party with external KUB '
                            f'ID {org_id} not found (created from Fraktion).'
                        )
                        continue
                    group = self.parliamentary_group_map.get(org_id)

                    # Use role_key_type hint for the variable
                    current_role_key = (
                        parliamentarian.id,
                        party.id if party else None,
                        group.id if group else None,
                        'member',  # Role type
                        None,  # additional_information
                    )
                    existing_role = existing_roles_map.get(current_role_key)

                    start_val = membership.get('start')
                    start_date_str = (
                        str(start_val)
                        if start_val and not isinstance(start_val, bool)
                        else None
                    )
                    end_val = membership.get('end')
                    end_date_str = (
                        str(end_val)
                        if end_val and not isinstance(end_val, bool)
                        else None
                    )

                    if existing_role:
                        # Update existing role
                        updated = self._update_parliamentarian_role(
                            existing_role,
                            role='member',
                            parliamentary_group=group,
                            parliamentary_group_role=self._map_to_parliamentary_group_role(
                                role_text
                            ),
                            party=party,
                            party_role=('member' if party else 'none'),
                            start_date=start_date_str,
                            end_date=end_date_str,
                        )
                        if updated:
                            parliamentarian_roles_to_update.append(
                                existing_role
                            )
                            log.debug(
                                f'Updating Fraktion/Party role for '
                                f'{parliamentarian.id}'
                            )
                        # No need to append, session flush handles updates.
                    else:
                        # Create new role
                        role_obj = self._create_parliamentarian_role(
                            parliamentarian=parliamentarian,
                            role='member',
                            parliamentary_group=group,
                            parliamentary_group_role=self._map_to_parliamentary_group_role(
                                role_text
                            ),
                            party=party,
                            party_role=('member' if party else 'none'),
                            start_date=start_date_str,
                            end_date=end_date_str,
                        )
                        if role_obj:
                            parliamentarian_roles_to_create.append(role_obj)
                            # Add the new role to the map
                            # Ensure the key matches RoleKey type
                            if parliamentarian.id:
                                current_role_key_after_create: (
                                    role_key_type
                                ) = (
                                    parliamentarian.id,
                                    role_obj.party_id,
                                    role_obj.parliamentary_group_id,
                                    role_obj.role,
                                    role_obj.additional_information,
                                )
                                existing_roles_map[
                                    current_role_key_after_create
                                ] = role_obj
                            log.debug(
                                f'Creating Fraktion/Party role for '
                                f'{parliamentarian.id}'
                            )

                elif org_type_title == 'Kantonsrat':
                    processed_counts['parliamentarian_roles'] += 1
                    processed_membership_type = True
                    role = self._map_to_parliamentarian_role(role_text)
                    start_val = membership.get('start')
                    start_date_str = (
                        str(start_val)
                        if start_val and not isinstance(start_val, bool)
                        else None
                    )
                    end_val = membership.get('end')
                    end_date_str = (
                        str(end_val)
                        if end_val and not isinstance(end_val, bool)
                        else None
                    )

                    current_role_key = (
                        parliamentarian.id,
                        None,  # party_id
                        None,  # group_id
                        role,  # Actual role from _map_to_parliamentarian_role
                        None,  # additional_information
                    )
                    existing_role = existing_roles_map.get(current_role_key)

                    if existing_role:
                        updated = self._update_parliamentarian_role(
                            existing_role,
                            role=role,
                            start_date=start_date_str,
                            end_date=end_date_str,
                        )
                        if updated:
                            parliamentarian_roles_to_update.append(
                                existing_role
                            )
                            log.debug(
                                f'Updating Kantonsrat role ({role}) for '
                                f'{parliamentarian.id}'
                            )
                        # No need to append, session flush handles updates.
                    else:
                        role_obj = self._create_parliamentarian_role(
                            parliamentarian=parliamentarian,
                            role=role,
                            start_date=start_date_str,
                            end_date=end_date_str,
                        )
                        if role_obj:
                            parliamentarian_roles_to_create.append(role_obj)
                            # Add the new role to the map
                            # Ensure the key matches RoleKey type
                            if parliamentarian.id:
                                current_role_key_after_create = (
                                    parliamentarian.id,
                                    role_obj.party_id,
                                    role_obj.parliamentary_group_id,
                                    role_obj.role,
                                    role_obj.additional_information,
                                )
                                existing_roles_map[
                                    current_role_key_after_create
                                ] = role_obj
                            log.debug(
                                f'Creating Kantonsrat role ({role}) for '
                                f'{parliamentarian.id}'
                            )

                elif org_type_title == 'Sonstige':
                    processed_counts['parliamentarian_roles'] += 1
                    processed_membership_type = True
                    additional_info = f'{role_text} - {org_name}'
                    start_val = membership.get('start')
                    start_date_str = (
                        str(start_val)
                        if start_val and not isinstance(start_val, bool)
                        else None
                    )
                    end_val = membership.get('end')
                    end_date_str = (
                        str(end_val)
                        if end_val and not isinstance(end_val, bool)
                        else None
                    )

                    current_role_key = (  # type: ignore[assignment]
                        parliamentarian.id,
                        None,  # party_id
                        None,  # group_id
                        'member',  # Role type
                        additional_info,  # additional_information
                    )
                    existing_role = existing_roles_map.get(current_role_key)

                    if existing_role:
                        updated = self._update_parliamentarian_role(
                            existing_role,
                            role='member',
                            additional_information=additional_info,
                            start_date=start_date_str,
                            end_date=end_date_str,
                        )
                        if updated:
                            parliamentarian_roles_to_update.append(
                                existing_role
                            )
                            log.debug(
                                f'Updating Sonstige role for '
                                f'{parliamentarian.id}: {additional_info}'
                            )
                        # No need to append, session flush handles updates.
                    else:
                        role_obj = self._create_parliamentarian_role(
                            parliamentarian=parliamentarian,
                            role='member',
                            additional_information=additional_info,
                            start_date=start_date_str,
                            end_date=end_date_str,
                        )
                        if role_obj:
                            parliamentarian_roles_to_create.append(role_obj)
                            # Add the new role to the map
                            # Ensure the key matches RoleKey type
                            if parliamentarian.id:
                                current_role_key_after_create = (
                                    parliamentarian.id,
                                    role_obj.party_id,
                                    role_obj.parliamentary_group_id,
                                    role_obj.role,
                                    role_obj.additional_information,
                                )
                                existing_roles_map[
                                    current_role_key_after_create
                                ] = role_obj
                            log.debug(
                                f'Creating Sonstige role for '
                                f'{parliamentarian.id}: {additional_info}'
                            )
                else:
                    # Count skipped/unknown types
                    if not processed_membership_type:
                        processed_counts['skipped'] += 1
                    log.warning(
                        f'Skipping membership: Unknown organization type '
                        f"'{org_type_title}' "
                        f'for organization {org_name}'
                    )

            except Exception as e:
                # Use initialized person_id for logging
                log_person_id = person_id if person_id else 'unknown'
                log.error(
                    f'Error creating membership for '
                    f'person_id {log_person_id}: {e}',
                    exc_info=True,
                )
                # Count errors as skipped if not already counted
                if not processed_membership_type:
                    processed_counts['skipped'] += 1

        # Save newly created memberships and roles
        if commission_memberships_to_create:
            self._bulk_save(
                commission_memberships_to_create, 'new commission memberships'
            )
        if parliamentarian_roles_to_create:
            self._bulk_save(
                parliamentarian_roles_to_create, 'new parliamentarian roles'
            )

        # Flush is removed, commit at the end of import_zug_kub_data
        # IDs will be assigned after the final commit.
        try:
            # Populate details based on object existence, not internal ID yet
            details['commission_memberships']['created'] = list(
                commission_memberships_to_create
            )
            details['commission_memberships']['updated'] = list(
                commission_memberships_to_update
            )
            details['parliamentarian_roles']['created'] = list(
                parliamentarian_roles_to_create
            )
            details['parliamentarian_roles']['updated'] = list(
                parliamentarian_roles_to_update
            )

            # Update processed counts in the details dictionary
            details['commission_memberships']['processed'] = processed_counts[
                'commission_memberships'
            ]
            details['parliamentarian_roles']['processed'] = processed_counts[
                'parliamentarian_roles'
            ]

        except Exception:
            log.error('Error flushing memberships/roles', exc_info=True)
            self.session.rollback()
            # Clear lists on error, but keep processed counts
            details['commission_memberships'] = {
                'created': [],
                'updated': [],
                'processed': processed_counts['commission_memberships'],
            }
            details['parliamentarian_roles'] = {
                'created': [],
                'updated': [],
                'processed': processed_counts['parliamentarian_roles'],
            }

        log.info(
            f'Membership/Role import details: '
            f'CMs(C:{len(details["commission_memberships"]["created"])}, '
            f'U:{len(details["commission_memberships"]["updated"])}, '
            f'P:{details["commission_memberships"]["processed"]}), '
            f'Roles(C:{len(details["parliamentarian_roles"]["created"])}, '
            f'U:{len(details["parliamentarian_roles"]["updated"])}, '
            f'P:{details["parliamentarian_roles"]["processed"]}), '
            f'Skipped: {processed_counts["skipped"]}'
        )
        return details, processed_counts

    def _create_commission_membership(
        self,
        parliamentarian: PASParliamentarian,
        commission: PASCommission,
        membership_data: MembershipData,
    ) -> PASCommissionMembership | None:
        """Create a CommissionMembership object."""
        try:
            if not parliamentarian.id or not commission.id:
                log.warning(
                    f'Missing ID: Parliamentarian={parliamentarian.id}, '
                    f'Commission={commission.id}'
                )
                return None

            role_text = membership_data.get('role', '')
            role = self._map_to_commission_role(role_text)

            start = membership_data.get('start')
            end = membership_data.get('end')

            start_date = self.parse_date(
                str(start) if start and not isinstance(start, bool) else None
            )
            end_date = self.parse_date(
                str(end) if end and not isinstance(end, bool) else None
            )

            assert parliamentarian.id is not None
            assert commission.id is not None
            return PASCommissionMembership(
                parliamentarian=parliamentarian,
                parliamentarian_id=parliamentarian.id,
                commission=commission,
                commission_id=commission.id,
                role=role,
                start=start_date,
                end=end_date,
            )
        except Exception as e:
            log.error(
                f'Error creating commission membership: {e}', exc_info=True
            )
            return None

    def _update_commission_membership(
        self,
        membership: PASCommissionMembership,
        membership_data: MembershipData
    ) -> bool:
        """
        Updates an existing CommissionMembership object.
        Returns True if changed.
        """
        changed = False
        new_role = self._map_to_commission_role(
            membership_data.get('role', '')
        )
        start_val = membership_data.get('start')
        new_start = self.parse_date(
            str(start_val)
            if start_val and not isinstance(start_val, bool)
            else None
        )
        end_val = membership_data.get('end')
        new_end = self.parse_date(
            str(end_val) if end_val and not isinstance(end_val, bool) else None
        )

        if membership.role != new_role:
            membership.role = new_role
            changed = True
        if membership.start != new_start:
            membership.start = new_start
            changed = True
        if membership.end != new_end:
            membership.end = new_end
            changed = True

        return changed

    def _create_parliamentarian_role(
        self,
        parliamentarian: PASParliamentarian,
        role: Role,
        parliamentary_group: PASParliamentaryGroup | None = None,
        parliamentary_group_role: ParliamentaryGroupRole | None = None,
        party: Party | None = None,
        party_role: PartyRole | None = None,
        additional_information: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> PASParliamentarianRole | None:
        try:
            # Ensure parliamentarian has an ID
            if not parliamentarian.id:
                log.warning(
                    'Skipping parliamentarian role: '
                    'PASParliamentarian missing '
                    f'ID: {parliamentarian.first_name} '
                    f'{parliamentarian.last_name}'
                )
                return None

            assert parliamentarian.id is not None
            return PASParliamentarianRole(
                parliamentarian=parliamentarian,
                parliamentarian_id=parliamentarian.id,
                role=role,
                parliamentary_group=parliamentary_group,
                parliamentary_group_role=parliamentary_group_role or 'none',
                party=party,
                party_role=party_role or 'none',
                additional_information=additional_information,
                start=self.parse_date(start_date),
                end=self.parse_date(end_date),
            )
        except Exception as e:
            log.error(
                f'Error creating parliamentarian role: {e}', exc_info=True
            )
            return None

    def _update_parliamentarian_role(
        self,
        role_obj: PASParliamentarianRole,
        role: Role,
        parliamentary_group: PASParliamentaryGroup | None = None,
        parliamentary_group_role: ParliamentaryGroupRole | None = None,
        party: Party | None = None,
        party_role: PartyRole | None = None,
        additional_information: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> bool:
        """
        Updates an existing ParliamentarianRole object.
        Returns True if changed.
        """
        changed = False
        new_start = self.parse_date(start_date)
        new_end = self.parse_date(end_date)

        # Update fields only if they are provided for the specific role type
        if role_obj.role != role:
            role_obj.role = role
            changed = True
        # Update related objects if provided
        if (
            parliamentary_group is not None
            and role_obj.parliamentary_group != parliamentary_group
        ):
            role_obj.parliamentary_group = parliamentary_group
            changed = True
        new_group_role = parliamentary_group_role or 'none'
        if role_obj.parliamentary_group_role != new_group_role:
            role_obj.parliamentary_group_role = new_group_role
            changed = True
        if party is not None and role_obj.party != party:
            role_obj.party = party
            changed = True
        new_party_role = party_role or 'none'
        if role_obj.party_role != new_party_role:
            role_obj.party_role = new_party_role
            changed = True
        if (
            additional_information is not None
            and role_obj.additional_information != additional_information
        ):
            role_obj.additional_information = additional_information
            changed = True
        if role_obj.start != new_start:
            role_obj.start = new_start
            changed = True
        if role_obj.end != new_end:
            role_obj.end = new_end
            changed = True

        return changed

    def _map_to_commission_role(
        self, role_text: str
    ) -> Literal['president', 'extended_member', 'guest', 'member']:
        """Map a role text to a CommissionMembership role enum value."""
        role_text = role_text.lower().strip()

        if 'präsident' in role_text:
            return 'president'
        if 'erweitert' in role_text:  # Check specific terms first
            return 'extended_member'
        if 'gast' in role_text:
            return 'guest'
        # Default to 'member' if none of the above match
        return 'member'

    def _map_to_parliamentarian_role(self, role_text: str) -> Role:
        """Map a role text to a parliamentarian role enum value."""
        role_text = role_text.lower().strip()

        # Order matters: check more specific roles first
        if 'präsident' in role_text:
            return 'president'
        if any(
            term in role_text for term in ['stimmenzähler', 'vote counter']
        ):
            return 'vote_counter'
        # 'vizepräsident' maps to 'member' as per model/data
        if any(
            term in role_text
            for term in [
                'vizepräsident',
                'vize-präsident',
                'vize präsident',
            ]
        ):
            return 'member'
        # Default to 'member' if none of the specific roles match
        return 'member'

    def _map_to_parliamentary_group_role(
        self, role_text: str
    ) -> ParliamentaryGroupRole | None:
        """Map a role text to a ParliamentaryGroupRole enum value."""
        role_text = role_text.lower().strip()

        # Order matters: check more specific roles first
        if 'präsident' in role_text:
            return 'president'
        if any(
            term in role_text for term in ['stimmenzähler', 'vote counter']
        ):
            return 'vote_counter'
        # 'vizepräsident' maps to 'member' as per model/data
        if any(
            term in role_text
            for term in [
                'vizepräsident',
                'vize-präsident',
                'vize präsident',
            ]
        ):
            return 'member'
        # Check for 'mitglied' explicitly if needed, else covered by default
        if 'mitglied' in role_text:
            return 'member'

        # Default to 'none' if no specific role is identified
        return 'none'

    @classmethod
    def extract_role_org_type_pairs(
        cls, memberships_data: Sequence[MembershipData]
    ) -> list[str]:
        """Extract unique combinations of role and organizationTypeTitle
        from JSON data. Useful way to get an overview of the data."""
        combinations = set()
        for membership in memberships_data:
            if (
                membership.get('role')
                and membership.get('organization')
                and membership['organization'].get('organizationTypeTitle')
            ):
                otype = membership['organization']['organizationTypeTitle']
                pair = f'{membership["role"]} - {otype}'
                combinations.add(pair)

        return sorted(combinations)


def count_unique_fullnames(
    people_data: list[Any],
    organizations_data: list[Any],
    memberships_data: list[Any],
) -> set[str]:
    """Counts unique 'fullName' entries across different data structures."""

    all_names: set[str] = set()

    def extract_full_names(data: Sequence[Any]) -> None:
        """Recursively extracts 'fullName' from nested dicts/lists."""
        for item in data:
            if isinstance(item, dict):
                if 'fullName' in item and isinstance(item['fullName'], str):
                    all_names.add(item['fullName'])
                # Recurse into values that are lists or dicts
                for value in item.values():
                    if isinstance(value, (dict, list)):
                        # Pass as sequence if list, wrap dict in list
                        extract_full_names(
                            [value] if isinstance(value, dict) else value
                        )
            elif isinstance(item, list):
                # If the top-level item is a list, recurse into it
                extract_full_names(item)

    # Process each top-level data list
    extract_full_names(people_data)
    extract_full_names(organizations_data)
    extract_full_names(memberships_data)

    return all_names
