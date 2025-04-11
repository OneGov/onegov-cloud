from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TypedDict, cast, Union
from typing import TYPE_CHECKING
from os import PathLike

from sqlalchemy.orm import Session

from onegov.pas.models.commission_membership import (
    ROLES as MEMBERSHIP_ROLES,
    CommissionMembership,
)
from onegov.pas.models import (
    Parliamentarian,
    Commission,
    ParliamentaryGroup,
    Party,
    ParliamentarianRole,
)

if TYPE_CHECKING:
    from onegov.pas.models.parliamentarian_role import ParliamentaryGroupRole
    from onegov.pas.models.parliamentarian_role import PartyRole
    from onegov.pas.models.parliamentarian_role import Role
    from sqlalchemy.orm import Session
    from collections.abc import Sequence, Mapping
    from datetime import date
    from io import IOBase

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
        organization: OrganizationData
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


def determine_membership_role(membership_data: dict[str, Any]) -> str:
    role = membership_data.get('role', '').lower()
    role_mappings = {
        k: k for k in MEMBERSHIP_ROLES.keys()
    }  # Use enum keys directly
    return role_mappings.get(role, 'member')


class DataImporter:
    """Base class for all importers with common functionality."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def parse_date(
        self,
        date_string: str | None,
    ) -> date | None:  # Return date type
        # Should convert to date if needed for model fields
        if not date_string:
            return None
        try:
            dt = datetime.fromisoformat(date_string.rstrip('Z'))
            return dt.date()  # Convert to date object
        except ValueError:
            logging.warning(f'Could not parse date string: {date_string}')
            return None

    def _bulk_save(self, objects: list[Any], object_type: str) -> None:
        """Save a batch of objects to the database."""
        try:
            if objects:
                # self.session.bulk_save_objects(objects)
                self.session.add_all(objects)
                self.session.flush()  # Flush to get IDs

                logging.info(f'Imported {len(objects)} {object_type}')
        except Exception as e:
            logging.error(
                f'Error bulk saving {object_type}: {e}', exc_info=True
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

    # key is the external name, value is the name we use for that
    person_attribute_map: dict[str, str] = {
        'id': 'external_kub_id',
        'firstName': 'first_name',
        'officialName': 'last_name',
        'title': 'academic_title',
        'salutation': 'salutation',
    }

    def bulk_import(
        self, people_data: Sequence[PersonData]
    ) -> dict[str, Parliamentarian]:
        """Imports people from JSON data and returns a map of id to
        Parliamentarian."""
        parliamentarians = []
        parliamentarian_map: dict[
            str, Parliamentarian
        ] = {}  # Map to store parliamentarians by ID

        for person_data in people_data:
            try:
                parliamentarian = self._create_parliamentarian(person_data)
                if parliamentarian:
                    parliamentarians.append(parliamentarian)
                    parliamentarian_map[person_data['id']] = (
                        parliamentarian  # Store in map
                    )
            except Exception as e:
                logging.error(
                    f'Error importing person with id '
                    f'{person_data.get("id")}: {e}',
                    exc_info=True,
                )

        self._bulk_save(parliamentarians, 'parliamentarians')
        return parliamentarian_map

    def _create_parliamentarian(
        self, person_data: PersonData
    ) -> Parliamentarian | None:
        """Creates a single Parliamentarian object from person data."""

        if not person_data.get('id'):  # Basic validation
            logging.error(
                f'Skipping person due to missing ID: '
                f'{person_data.get("fullName")}'
            )
            return None

        parliamentarian_kwargs = {}
        for json_key, model_attr in self.person_attribute_map.items():
            if (val := person_data.get(json_key)):
                parliamentarian_kwargs[model_attr] = val
            else:
                breakpoint()

        # Handle nested primaryEmail
        primary_email_data = person_data.get('primaryEmail')
        if primary_email_data and primary_email_data.get('email'):
            parliamentarian_kwargs['email_primary'] = primary_email_data[
                'email'
            ]

        parliamentarian = Parliamentarian(**parliamentarian_kwargs)
        return parliamentarian


class OrganizationImporter(DataImporter):
    """Importer for organization data from organizations.json."""

    def bulk_import(
        self, organizations_data: Sequence[dict[str, Any]]
    ) -> tuple[
        dict[str, Commission],
        dict[str, ParliamentaryGroup],
        dict[str, Party],
        dict[str, Any],
    ]:
        """
        Imports organizations from JSON data.

        Returns:
            Tuple containing maps of external IDs to:
            - Commissions
            - Parliamentary Groups
            - Parties (created from parliamentary groups)
            - Other organizations
        """

        #  objects that will be saved
        commissions: list[Commission] = []
        parliamentary_groups: list[ParliamentaryGroup] = []
        parties: list[Party] = []

        # Maps to return
        other_organizations: dict[str, Any] = {}
        commission_map: dict[str, Commission] = {}
        parliamentary_group_map: dict[str, ParliamentaryGroup] = {}
        party_map: dict[str, Party] = {}

        for org_data in organizations_data:
            org_id = org_data.get('id')
            if not org_id:
                logging.error(
                    f'Skipping organization without ID: {org_data.get("name")}'
                )
                continue

            organization_type_title = org_data.get('organizationTypeTitle')
            org_name = org_data.get('name')

            try:
                if organization_type_title == 'Kommission':
                    commission = Commission(
                        external_kub_id=org_id,
                        name=org_data.get('name', ''),
                        type='normal',  # Default type
                    )
                    commissions.append(commission)
                    commission_map[org_id] = commission

                elif organization_type_title == 'Fraktion':
                    party_name = org_data.get('name', '')

                    # Kub-api scheint Parteien auch als Fraktionen zu
                    # bezeichnen, jedenfalls im organization_type_title!
                    party = Party(
                        external_kub_id=org_id,  # Assuming UUID conversion happens elsewhere
                        name=party_name,
                    )
                    parties.append(party)
                    party_map[party_name] = (
                        party  # Map by name for easy lookup
                    )
                    print('fraktion')

                elif organization_type_title in ('Kantonsrat', 'Sonstige'):
                    # Store these for reference in membership creation
                    other_organizations[org_id] = {
                        'id': org_id,
                        'name': org_data.get('name', ''),
                        'type': organization_type_title.lower(),
                    }
                elif org_name is not None and 'Legislatur' in org_name:
                    pass
                    # Can't create Legislatur objects here, as the api does
                    # not give us # the start / end date.
                else:
                    # check organization_type
                    logging.warning(
                        f'Unknown organization type: {organization_type_title}'
                        f' for {org_name}'
                    )

            except Exception as e:
                logging.error(
                    f'Error importing organization '
                    f'{org_data.get("name")}: {e}',
                    exc_info=True,
                )

        # Save to the database
        self._bulk_save(commissions, 'commissions')
        self._bulk_save(parliamentary_groups, 'parliamentary groups')
        self._bulk_save(parties, 'parties')

        return (
            commission_map,
            parliamentary_group_map,
            party_map,
            other_organizations,
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
        self.parliamentarian_map: dict[str, Parliamentarian] = {}
        self.commission_map: dict[str, Commission] = {}
        self.parliamentary_group_map: dict[str, ParliamentaryGroup] = {}
        self.party_map: dict[str, Party] = {}
        self.other_organization_map: dict[str, Any] = {}

    def init(
        self,
        session: Session,
        parliamentarian_map: dict[str, Parliamentarian],
        commission_map: dict[str, Commission],
        parliamentary_group_map: dict[str, ParliamentaryGroup],
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

    def _extract_and_create_missing_parliamentarians(
        self, memberships_data: Sequence[MembershipData]
    ) -> None:
        """Extract and create parliamentarians from membership data if they don't already exist."""
        new_parliamentarians = []
        temp_id_map = {}  # Temporary map to track external_id -> object

        for membership in memberships_data:
            try:
                person_data = membership['person']
                person_id = person_data.get('id')

                # Skip if already in map or missing ID
                if not person_id or person_id in self.parliamentarian_map:
                    continue

                logging.info(
                    f'Found parliamentarian in membership.json that '
                    f"wasn't in people data: {person_data.get('fullName')}"
                )

                # Create minimal parliamentarian object
                # Note: external_kub_id expects UUID but we're passing str
                # This should be fixed at the model level or by converting here
                from uuid import UUID
                try:
                    uuid_value = UUID(person_id) if person_id else None
                    parliamentarian = Parliamentarian(
                        external_kub_id=uuid_value,
                        first_name=person_data.get('firstName', ''),
                        last_name=person_data.get('officialName', ''),
                        salutation=person_data.get('salutation'),
                        academic_title=person_data.get('title'),
                    )
                except ValueError:
                    # Handle the case where person_id is not a valid UUID
                    logging.warning(f'Invalid UUID format for person_id: {person_id}')
                    parliamentarian = Parliamentarian(
                        first_name=person_data.get('firstName', ''),
                        last_name=person_data.get('officialName', ''),
                        salutation=person_data.get('salutation'),
                        academic_title=person_data.get('title'),
                    )

                # Handle email if present
                primary_email_data = person_data.get('primaryEmail')
                if primary_email_data and primary_email_data.get('email'):
                    parliamentarian.email_primary = primary_email_data['email']

                # Handle address if present
                address_data = membership.get('primaryAddress')
                if address_data:
                    parliamentarian.shipping_address = (
                        f'{address_data.get("street", "")} '
                        f'{address_data.get("houseNumber", "")}'.strip()
                    )
                    parliamentarian.shipping_address_zip_code = (
                        address_data.get('swissZipCode')
                    )
                    parliamentarian.shipping_address_city = address_data.get(
                        'town'
                    )

                # Add to collection and temp map
                new_parliamentarians.append(parliamentarian)
                temp_id_map[person_id] = parliamentarian

            except Exception as e:
                logging.error(
                    f'Error extracting parliamentarian from membership: {e}',
                    exc_info=True,
                )

        # Bulk save the new parliamentarians
        if new_parliamentarians:
            # Don't use bulk_save_objects as it doesn't update the objects with
            # IDs Instead use add_all which maintains the object references
            self.session.add_all(new_parliamentarians)
            self.session.flush()  # Flush to get IDs

            # Now update the parliamentarian_map with these objects that now
            # have IDs
            for external_id, parliamentarian in temp_id_map.items():
                self.parliamentarian_map[external_id] = parliamentarian

            logging.info(
                f'Created {len(new_parliamentarians)} parliamentarians from '
                        'membership data'
            )

    def bulk_import(self, memberships_data: Sequence[MembershipData]) -> None:
        """Imports memberships from JSON data based on organization type."""
        commission_memberships = []
        parliamentarian_roles = []

        # Loop over the wohle thing once, collecting only parliamentarians.
        self._extract_and_create_missing_parliamentarians(memberships_data)

        for membership in memberships_data:
            try:
                person_id = membership['person']['id']
                org_id = membership['organization']['id']

                parliamentarian = self.parliamentarian_map.get(person_id)
                if not parliamentarian:
                    logging.warning(
                        f'Skipping membership: Parliamentarian with external '
                        f'KUB ID {person_id} not found.'
                    )
                    continue

                organization_data = membership['organization']
                org_type_title = organization_data.get('organizationTypeTitle')
                role_text = membership.get('role', '')
                org_name = organization_data.get('name', '')

                if org_type_title == 'Kommission':
                    commission = self.commission_map.get(org_id)
                    if not commission:
                        logging.warning(
                            f'Skipping commission membership: Commission with '
                            f'external KUB ID {org_id} not found.'
                        )
                        continue

                    membership_obj = self._create_commission_membership(
                        parliamentarian, commission, membership
                    )
                    if membership_obj:
                        commission_memberships.append(membership_obj)

                elif org_type_title == 'Fraktion':
                    group = self.parliamentary_group_map.get(org_id)
                    if not group:
                        logging.warning(
                            f'Skipping parliamentary group role: Group '
                            f'with external KUB ID {org_id} not found.'
                        )
                        continue

                    # todo (cyrill):
                    # is org_name actually the right key for this
                    party = self.party_map.get(org_name)
                    breakpoint()
                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role='member',  # Default role for being in parliament
                        parliamentary_group=group,
                        parliamentary_group_role=self._map_to_parliamentary_group_role(role_text),
                        party=party,
                        party_role=(
                            'member' if party else 'none'
                        ),  # Default party role
                        start_date=str(membership.get('start')) if membership.get('start') and not isinstance(membership.get('start'), bool) else None,
                        end_date=str(membership.get('end')) if membership.get('end') and not isinstance(membership.get('end'), bool) else None,
                    )
                    if role_obj:
                        parliamentarian_roles.append(role_obj)

                elif org_type_title == 'Kantonsrat':
                    # Important: Kantonsrat represents the general parliament membership
                    role = self._map_to_parliamentarian_role(role_text)

                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role=role,
                        start_date=str(membership.get('start')) if membership.get('start') and not isinstance(membership.get('start'), bool) else None,
                        end_date=str(membership.get('end')) if membership.get('end') and not isinstance(membership.get('end'), bool) else None,
                    )
                    if role_obj:
                        parliamentarian_roles.append(role_obj)

                elif org_type_title == 'Sonstige':
                    # For 'Sonstige', store the role info in
                    # additional_information
                    additional_info = f'{role_text} - {org_name}'

                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role='member',  # Default role
                        additional_information=additional_info,
                        start_date=str(membership.get('start')) if membership.get('start') and not isinstance(membership.get('start'), bool) else None,
                        end_date=str(membership.get('end')) if membership.get('end') and not isinstance(membership.get('end'), bool) else None,
                    )
                    if role_obj:
                        parliamentarian_roles.append(role_obj)
                else:
                    logging.warning(
                        f'Skipping membership: Unknown organization type '
                        f'{org_type_title} '
                        f'for organization {org_name}'
                    )

            except Exception as e:
                person_id = membership.get('person', {}).get('id', 'unknown')
                logging.error(
                    f'Error creating membership for '
                    f'person_id {person_id}: {e}',
                    exc_info=True,
                )

        # Save all created objects to the database
        if commission_memberships:
            self._bulk_save(commission_memberships, 'commission memberships')
        if parliamentarian_roles:
            self._bulk_save(parliamentarian_roles, 'parliamentarian roles')

    def _create_commission_membership(
        self,
        parliamentarian: Parliamentarian,
        commission: Commission,
        membership_data: MembershipData,
    ) -> CommissionMembership | None:
        """Create a CommissionMembership object."""
        try:
            # Ensure both objects have IDs
            if not parliamentarian.id or not commission.id:
                logging.warning(
                    f'Missing ID: Parliamentarian={parliamentarian.id}, '
                    'Commission={commission.id}'
                )
                return None

            role_text = membership_data.get('role', '')
            role = self._map_to_commission_role(role_text)

            start = membership_data.get('start')
            end = membership_data.get('end')

            start_date = self.parse_date(
                str(start) if start and not isinstance(start, bool) else None)
            end_date = self.parse_date(
                str(end) if end and not isinstance(end, bool) else None)

            assert parliamentarian.id is not None
            assert commission.id is not None
            return CommissionMembership(
                parliamentarian=parliamentarian,
                parliamentarian_id=parliamentarian.id,
                commission=commission,
                commission_id=commission.id,
                role=role,
                start=start_date,
                end=end_date,
            )
        except Exception as e:
            logging.error(
                f'Error creating commission membership: {e}', exc_info=True
            )
            return None

    def _create_parliamentarian_role(
        self,
        parliamentarian: Parliamentarian,
        role: Role,
        parliamentary_group: ParliamentaryGroup | None = None,
        parliamentary_group_role: ParliamentaryGroupRole | None = None,
        party: Party | None = None,
        party_role: PartyRole | None = None,
        additional_information: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> ParliamentarianRole | None:
        try:
            # Ensure parliamentarian has an ID
            if not parliamentarian.id:
                logging.warning(
                    'Skipping parliamentarian role: Parliamentarian missing '
                    f'ID: {parliamentarian.first_name} '
                    f'{parliamentarian.last_name}'
                )
                return None

            assert parliamentarian.id is not None
            return ParliamentarianRole(
                parliamentarian=parliamentarian,
                parliamentarian_id=parliamentarian.id,  # Explicitly set the ID
                role=role,
                parliamentary_group=parliamentary_group,
                parliamentary_group_role=parliamentary_group_role,
                party=party,
                party_role=party_role,
                additional_information=additional_information,
                start=self.parse_date(start_date),
                end=self.parse_date(end_date),
            )
        except Exception as e:
            logging.error(
                f'Error creating parliamentarian role: {e}', exc_info=True
            )
            return None

    def _map_to_commission_role(
        self, role_text: str
    ) -> Literal['president', 'extended_member', 'guest', 'member']:
        """Map a role text to a CommissionMembership role enum value."""
        role_text = role_text.lower()

        if 'präsident' in role_text:
            return 'president'
        elif 'erweitert' in role_text:
            return 'extended_member'
        elif 'gast' in role_text:
            return 'guest'
        else:
            return 'member'

    def _map_to_parliamentarian_role(
        self, role_text: str
    ) -> Role:
        """Map a role text to a parliamentarian role enum value."""
        role_text = role_text.lower()

        # These keys must match the enum values in PARLIAMENTARIAN_ROLES
        if 'präsident' in role_text:
            return 'president'
        elif any(
            term in role_text
            for term in [
                'vizepräsident',
                'vize-präsident',
                'vize präsident',
            ]
        ):
            return 'vice_president'
        elif any(
            term in role_text for term in ['stimmenzähler', 'vote counter']
        ):
            return 'vote_counter'
        else:
            return 'member'

    def _map_to_parliamentary_group_role(
        self, role_text: str
    ) -> Role:
        """Map a role text to a parliamentary_group_role enum value."""
        role_text = role_text.lower()

        # These keys must match the enum values in PARLIAMENTARY_GROUP_ROLES
        if 'präsident' in role_text:
            return 'president'
        elif any(
            term in role_text
            for term in [
                'vizepräsident',
                'vize-präsident',
                'vize präsident',
            ]
        ):
            return 'vice_president'
        elif any(
            term in role_text for term in ['stimmenzähler', 'vote counter']
        ):
            return 'vote_counter'
        elif 'mitglied' in role_text:
            return 'member'

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
    """Just used to verify we actually get the value we expected."""

    def extract_full_names(data: dict[str, Any] | list[Any]) -> set[str]:
        full_names = set()

        def traverse(obj: Any) -> None:
            if isinstance(obj, dict):
                if 'fullName' in obj and isinstance(obj['fullName'], str):
                    full_names.add(obj['fullName'])
                for value in obj.values():
                    traverse(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)

        traverse(data)
        return full_names

    people_names = extract_full_names(people_data)
    org_names = extract_full_names(organizations_data)
    membership_names = extract_full_names(memberships_data)
    all_names = people_names.union(org_names, membership_names)
    return all_names


def import_zug_kub_data(
    session: Session,
    people_data: Sequence[PersonData],
    organization_data: Sequence[OrganizationData],
    membership_data: Sequence[MembershipData],
) -> None:
    people_importer = PeopleImporter(session)
    parliamentarian_map = people_importer.bulk_import(people_data)

    organization_importer = OrganizationImporter(session)
    (
        commission_map,
        parliamentary_group_map,
        party_map,
        other_organization_map,
    ) = organization_importer.bulk_import(organization_data)

    membership_importer = MembershipImporter(session)
    membership_importer.init(
        session,
        parliamentarian_map,
        commission_map,
        parliamentary_group_map,
        party_map,
        other_organization_map,
    )
    membership_importer.bulk_import(membership_data)
