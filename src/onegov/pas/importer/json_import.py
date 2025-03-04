from __future__ import annotations

from sqlalchemy.orm import Session
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Self, Literal


import logging

from onegov.pas.constants import COMMON_PARTY_NAMES
from onegov.pas.models.commission_membership import (
    ROLES as MEMBERSHIP_ROLES,
    CommissionMembership,
)

from onegov.pas.models import (
    Parliamentarian,
    Commission,
    ParliamentaryGroup,
    Party,
    ParliamentarianRole
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from collections.abc import Sequence
    from typing import TypedDict, Literal
    from _typeshed import StrOrBytesPath

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
        organizationTypeTitle: Literal[
            'Kommission', 'Fraktion', 'Kantonsrat', 'Sonstige'
        ]
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

    OrganizationType = Literal[
        'Kommission', 'Kantonsrat', 'Fraktion', 'Sonstige'
    ]


def determine_membership_role(membership_data: dict[str, Any]) -> str:
    role = membership_data.get('role', '').lower()
    role_mappings = {
        k: k for k in MEMBERSHIP_ROLES.keys()
    }  # Use enum keys directly
    return role_mappings.get(role, 'member')


def _load_json(source: StrOrBytesPath) -> list[Any]:
    if isinstance(source, (str, Path)):
        with open(source, encoding='utf-8') as f:
            return json.load(f)['results']  # Assuming 'results' key
    elif hasattr(source, 'read'):  # File-like object
        return json.load(source)['results']  # Assuming 'results' key
    else:
        raise TypeError('Invalid source type')


class DataImporter:
    """Base class for all importers with common functionality."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def parse_date(
        self: Self,
        date_string: str | None,
    ) -> datetime | None:  # Return datetime, not date
        if not date_string:
            return None
        try:
            dt = datetime.fromisoformat(date_string.rstrip('Z'))
            return dt
        except ValueError:
            logging.warning(f'Could not parse date string: {date_string}')
            return None

    def _bulk_save(self, objects: list[Any], object_type: str) -> None:
        """Generic bulk save method with error handling."""
        try:
            self.session.bulk_save_objects(objects)
            logging.info(f'Imported {len(objects)} {object_type}')
        except Exception as e:
            logging.error(
                f'Error bulk saving {object_type}: {e}', exc_info=True
            )
            self.session.rollback()  # Rollback on error during bulk save
            raise


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
        parliamentarian_map: dict[str, Parliamentarian] = (
            {}
        )  # Map to store parliamentarians by ID

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
            logging.warning(
                f"Skipping person due to missing ID: "
                f"{person_data.get('fullName')}"
            )
            return None

        # The parliamentarian `active` value needs to be taking into
        # consideration. This attribute is a dynamic attribute that
        # is computed at runtime based on the
        # ParliamentarianRoles and it's start / end timeframe

        # In the api however, this is a simple boolean value.
        # This is of course doesn't map easily, as we track
        # historical data while the `active` boolean is simply a
        # representation of how it is *now*.
        parliamentarian_kwargs = {}
        for json_key, model_attr in self.person_attribute_map.items():
            parliamentarian_kwargs[model_attr] = person_data.get(json_key)

        # Handle nested primaryEmail
        primary_email_data = person_data.get('primaryEmail')
        if primary_email_data and primary_email_data.get('email'):
            parliamentarian_kwargs['email_primary'] = primary_email_data[
                'email'
            ]

        parliamentarian = Parliamentarian(**parliamentarian_kwargs)
        return parliamentarian

    def _bulk_save(self, objects: list[Any], object_type: str) -> None:
        """Generic bulk save method with error handling."""
        try:
            self.session.bulk_save_objects(objects)
            logging.info(f'Imported {len(objects)} {object_type}')
            self.session.flush()  # Important to flush session to get IDs for
            # relationships
        except Exception as e:
            logging.error(
                f'Error bulk saving {object_type}: {e}', exc_info=True
            )
            self.session.rollback()
            raise


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
        commissions = []
        parliamentary_groups = []
        parties = []

        # Maps to return
        other_organizations = {}
        commission_map = {}
        parliamentary_group_map = {}
        party_map = {}

        for org_data in organizations_data:
            org_id = org_data.get('id')
            if not org_id:
                logging.warning(
                    f"Skipping organization without ID: {org_data.get('name')}"
                )
                continue

            organization_type_title = org_data.get('organizationTypeTitle')

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
                        external_kub_id=f'{org_id}',
                        name=party_name,
                    )
                    parties.append(party)
                    assert party_name in COMMON_PARTY_NAMES
                    party_map[party_name] = (
                        party  # Map by name for easy lookup
                    )

                elif organization_type_title in ('Kantonsrat', 'Sonstige'):
                    # Store these for reference in membership creation
                    other_organizations[org_id] = {
                        'id': org_id,
                        'name': org_data.get('name', ''),
                        'type': organization_type_title.lower(),
                    }

                else:
                    logging.warning(
                        f"Unknown organization type: {organization_type_title}"
                        f" for {org_data.get('name')}"
                    )

            except Exception as e:
                logging.error(
                    f"Error importing organization "
                    f"{org_data.get('name')}: {e}",
                    exc_info=True,
                )

        # Save to the database
        self._bulk_save(commissions, 'commissions')
        self._bulk_save(
            parliamentary_groups, 'parliamentary groups'
        )
        self._bulk_save(parties, 'parties')

        return (
            commission_map,
            parliamentary_group_map,
            party_map,
            other_organizations,
        )

    def _bulk_save(self, objects: list[Any], object_type: str) -> None:
        """Save a batch of objects to the database."""
        try:
            if objects:
                self.session.bulk_save_objects(objects)
                self.session.flush()  # Flush to get IDs
                logging.info(f'Imported {len(objects)} {object_type}')
        except Exception as e:
            logging.error(
                f'Error bulk saving {object_type}: {e}', exc_info=True
            )
            self.session.rollback()
            raise


class MembershipImporter(DataImporter):
    """Importer for membership data from memberships.json."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.parliamentarian_map = {}
        self.commission_map = {}
        self.parliamentary_group_map = {}
        self.party_map = {}
        self.other_organization_map = {}

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

    def bulk_import(
        self, memberships_data: Sequence[MembershipData]
    ) -> None:
        """Imports memberships from JSON data based on organization type."""
        commission_memberships = []
        parliamentarian_roles = []

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
                org_type_title = organization_data.get(
                    'organizationTypeTitle'
                )
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

                    party = self.party_map.get(org_name)
                    #  somehow  roles are created where party is none
                    breakpoint()

                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role='member',  # Default role for being in parliament
                        parliamentary_group=group,
                        parliamentary_group_role=self._map_to_parliamentary_group_role(
                            role_text
                        ),
                        party=party,
                        party_role=(
                            'member' if party else 'none'
                        ),  # Default party role
                        start_date=membership.get('start'),
                        end_date=membership.get('end'),
                    )
                    if role_obj:
                        parliamentarian_roles.append(role_obj)

                elif org_type_title == 'Kantonsrat':
                    # Kantonsrat represents the general parliament membership
                    role = self._map_to_parliamentarian_role(role_text)

                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role=role,
                        start_date=membership.get('start'),
                        end_date=membership.get('end'),
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
                        start_date=membership.get('start'),
                        end_date=membership.get('end'),
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
                person_id = membership.get('person', {}).get(
                    'id', 'unknown'
                )
                logging.error(
                    f'Error creating membership for '
                    f'person_id {person_id}: {e}', exc_info=True,
                )

        # Save all created objects to the database
        if commission_memberships:
            self._bulk_save(
                commission_memberships, 'commission memberships'
            )
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
            role_text = membership_data.get('role', '')
            role = self._map_to_commission_role(role_text)

            start_date = self.parse_date(membership_data.get('start'))
            end_date = self.parse_date(membership_data.get('end'))

            return CommissionMembership(
                parliamentarian=parliamentarian,
                commission=commission,
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
        role: str,
        parliamentary_group: ParliamentaryGroup = None,
        parliamentary_group_role: str = 'none',
        party: Party = None,
        party_role: str = 'none',
        additional_information: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> ParliamentarianRole | None:
        """Create a ParliamentarianRole object with the specified
        relationships."""
        try:
            return ParliamentarianRole(
                parliamentarian=parliamentarian,
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

    def _map_to_parliamentarian_role(self, role_text: str) -> str:
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

    def _map_to_parliamentary_group_role(self, role_text: str) -> str:
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

        raise ValueError(f'Unknown role text: {role_text}')

    def _bulk_save(self, objects: list[Any], object_type: str) -> list[Any]:
        """Save a batch of objects to the database."""
        try:
            if objects:
                breakpoint()
                self.session.bulk_save_objects(objects)
                first = objects[0]  # check role
                self.session.flush()  # Flush to get IDs
                logging.info(f'Imported {len(objects)} {object_type}')
        except Exception as e:
            logging.error(
                f'Error bulk saving {object_type}: {e}', exc_info=True
            )
            self.session.rollback()
            raise
        finally:
            return object_type or []


def import_zug_kub_data(
    session: Session,
    people_source: StrOrBytesPath,
    organizations_source: StrOrBytesPath,
    memberships_source: StrOrBytesPath,
) -> list[Any]:
    """Imports data from Zug KUB JSON sources."""

    people_data = _load_json(people_source)
    organization_data = _load_json(organizations_source)
    membership_data = _load_json(memberships_source)

    # Import people
    people_importer = PeopleImporter(session)
    parliamentarian_map = people_importer.bulk_import(people_data)

    # Import organizations
    organization_importer = OrganizationImporter(session)
    (
        commission_map,
        parliamentary_group_map,
        party_map,
        other_organization_map,
    ) = organization_importer.bulk_import(organization_data)

    # Import memberships
    membership_importer = MembershipImporter(session)
    membership_importer.init(
        session,
        parliamentarian_map,
        commission_map,
        parliamentary_group_map,
        party_map,
        other_organization_map,
    )

    return membership_importer.bulk_import(membership_data)

