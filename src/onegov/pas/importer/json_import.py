from __future__ import annotations

from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Self, Literal
from collections.abc import Sequence

from onegov.pas.models import (
    Parliamentarian,
    ParliamentaryGroup,
    Commission,
    ParliamentarianRole,
)
from onegov.pas.models.commission_membership import (
    ROLES as MEMBERSHIP_ROLES,
    CommissionMembership,
)


from typing import TextIO, TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath
    from sqlalchemy.orm import Session
    from typing import TypedDict
    from collections.abc import Sequence

    class EmailData(TypedDict):
        id: str
        label: str
        email: str
        isDefault: bool
        thirdPartyId: str | None
        modified: str
        created: str

    class PersonData(TypedDict):
        id: str
        firstName: str
        fullName: str
        officialName: str
        isActive: bool
        created: str
        modified: str
        personTypeTitle: str | None
        primaryEmail: EmailData | None
        salutation: str
        tags: list[str]
        thirdPartyId: str | None
        title: str
        username: str | None

    OrganizationType = Literal[
        'Kommission', 'Kantonsrat', 'Fraktion', 'Sonstige'
    ]

    class OrganizationData(TypedDict):
        id: str
        name: str
        description: str
        organizationTypeTitle: OrganizationType
        isActive: bool
        memberCount: int
        status: int
        created: str
        modified: str
        thirdPartyId: None | str
        primaryEmail: None | dict


def determine_membership_role(membership_data: dict[str, Any]) -> str:
    role = membership_data.get('role', '').lower()
    role_mappings = {
        k: k for k in MEMBERSHIP_ROLES.keys()
    }  # Use enum keys directly
    return role_mappings.get(role, 'member')


def _load_json(source: StrOrBytesPath) -> list[dict[str, Any]]:
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

    TL. DR: Some data for people is also pulled from memberships.json


    """

    # key is the external name, value is the name we use for that
    #
    # people_data json:
    # {'created': '2024-12-23T16:44:12.056040+01:00', 'firstName': 'Daniel',
    # 'fullName': 'Abt Daniel', 'id': 'd9403b52-d178-454c-8ac7-abb75af14aa6',
    # 'isActive': True, 'modified': '2024-12-23T16:44:12.056046+01:00',
    # 'officialName': 'Abt', 'personTypeTitle': None,
    # 'primaryEmail': {'id': 'c28dbad1-99fd-4694-8816-9c1bbd3dec72',
    # 'label': '1. E-Mail', 'email': 'da@example.org', 'isDefault': True,
    # 'thirdPartyId': None, 'modified': '2024-12-23T16:44:12.059162+01:00',
    # 'created': '2024-12-23T16:44:12.059150+01:00'}, 'salutation': 'Herr',
    # 'tags': [], 'thirdPartyId': '37', 'title': '', 'username': None}
    person_attribute_map: dict[str, str] = {
        'id': 'external_kub_id',
        'firstName': 'first_name',
        'officialName': 'last_name',
        'title': 'academic_title',
        'salutation': 'salutation',
        # 'primaryEmail.email': 'email_primary' #  Handle nested email separately
    }

    def bulk_import(
        self, people_data: Sequence[PersonData]
    ) -> dict[str, Parliamentarian]:
        """Imports people from JSON data and returns a map of id to Parliamentarian."""
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
            self.session.flush()  # Important to flush session to get IDs for relationships
        except Exception as e:
            logging.error(
                f'Error bulk saving {object_type}: {e}', exc_info=True
            )
            self.session.rollback()
            raise


MembershipRoleType = Literal[
    'none',
    'member',
    'votecounter',
    'vicepresident',
    'president',
    'president_parliamentary_group',
    'mediamanager',
]  # Combined role type hint

MembershipData = dict[str, Any]


class MembershipImporter:
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
        party_map: dict[str, Party] = None,
        other_organization_map: dict[str, Any] = None,
    ) -> None:
        """Initialize the importer with maps of objects by their external KUB ID."""
        self.session = session
        self.parliamentarian_map = parliamentarian_map
        self.commission_map = commission_map
        self.parliamentary_group_map = parliamentary_group_map
        self.party_map = party_map or {}
        self.other_organization_map = other_organization_map or {}

    def bulk_import(self, memberships_data: Sequence[MembershipData]) -> None:
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
                        f'Skipping membership: Parliamentarian with external KUB ID {person_id} not found.'
                    )
                    continue

                organization_data = membership['organization']
                org_type_title = organization_data.get('organizationTypeTitle')
                role_text = membership.get('role', '')

                if org_type_title == 'Kommission':
                    commission = self.commission_map.get(org_id)
                    if not commission:
                        logging.warning(
                            f'Skipping commission membership: Commission with external KUB ID {org_id} not found.'
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
                            f'Skipping parliamentary group role: Group with external KUB ID {org_id} not found.'
                        )
                        continue

                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role='member',  # Default for being in parliament
                        parliamentary_group=group,
                        parliamentary_group_role=self._map_to_parliamentary_group_role(role_text),
                        start_date=membership.get('start'),
                        end_date=membership.get('end')
                    )
                    if role_obj:
                        parliamentarian_roles.append(role_obj)

                elif org_type_title == 'Kantonsrat':
                    # Kantonsrat represents the general parliament
                    role = self._map_to_parliamentarian_role(role_text)

                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role=role,
                        start_date=membership.get('start'),
                        end_date=membership.get('end')
                    )
                    if role_obj:
                        parliamentarian_roles.append(role_obj)

                elif org_type_title == 'Sonstige':
                    # For 'Sonstige', store the role info in additional_information
                    org_name = organization_data.get('name', 'Unknown Organization')
                    additional_info = f"{role_text} - {org_name}"

                    role_obj = self._create_parliamentarian_role(
                        parliamentarian=parliamentarian,
                        role='member',  # Default role
                        additional_information=additional_info,
                        start_date=membership.get('start'),
                        end_date=membership.get('end')
                    )
                    if role_obj:
                        parliamentarian_roles.append(role_obj)

                else:
                    logging.warning(
                        f'Skipping membership: Unknown organization type {org_type_title} '
                        f'for organization {organization_data.get("name")}'
                    )

            except Exception as e:
                person_id = membership.get('person', {}).get('id', 'unknown')
                logging.error(
                    f'Error creating membership for person_id {person_id}: {e}',
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
        membership_data: MembershipData
    ) -> CommissionMembership | None:
        """Create a CommissionMembership object."""
        try:
            role_text = membership_data.get('role', '')
            role = self._map_to_commission_role(role_text)

            start_date = self._parse_date(membership_data.get('start'))
            end_date = self._parse_date(membership_data.get('end'))

            return CommissionMembership(
                parliamentarian=parliamentarian,
                commission=commission,
                role=role,
                start=start_date,
                end=end_date
            )
        except Exception as e:
            logging.error(f'Error creating commission membership: {e}', exc_info=True)
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
        end_date: str = None
    ) -> ParliamentarianRole | None:
        """Create a ParliamentarianRole object with the specified relationships."""
        try:
            return ParliamentarianRole(
                parliamentarian=parliamentarian,
                role=role,
                parliamentary_group=parliamentary_group,
                parliamentary_group_role=parliamentary_group_role,
                party=party,
                party_role=party_role,
                additional_information=additional_information,
                start=self._parse_date(start_date),
                end=self._parse_date(end_date)
            )
        except Exception as e:
            logging.error(f'Error creating parliamentarian role: {e}', exc_info=True)
            return None

    def _map_to_commission_role(self, role_text: str) -> str:
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
        elif any(term in role_text for term in ['vizepräsident', 'vize-präsident', 'vize präsident']):
            return 'vice_president'
        elif any(term in role_text for term in ['stimmenzähler', 'vote counter']):
            return 'vote_counter'
        else:
            return 'member'

    def _map_to_parliamentary_group_role(self, role_text: str) -> str:
        """Map a role text to a parliamentary_group_role enum value."""
        role_text = role_text.lower()

        # These keys must match the enum values in PARLIAMENTARY_GROUP_ROLES
        if 'präsident' in role_text:
            return 'president'
        elif any(term in role_text for term in ['vizepräsident', 'vize-präsident', 'vize präsident']):
            return 'vice_president'
        elif any(term in role_text for term in ['stimmenzähler', 'vote counter']):
            return 'vote_counter'
        else:
            return 'member'

    def _parse_date(self, date_string: str | None) -> datetime | None:
        """Parse a date string into a Python datetime object."""
        if not date_string:
            return None

        if date_string == 'False':  # Handle special case in API
            return None

        try:
            return datetime.fromisoformat(date_string.rstrip('Z'))
        except ValueError:
            logging.warning(f'Could not parse date string: {date_string}')
            return None

    def _bulk_save(self, objects: list[Any], object_type: str) -> None:
        """Save a list of objects to the database."""
        try:
            self.session.bulk_save_objects(objects)
            logging.info(f'Imported {len(objects)} {object_type}')
        except Exception as e:
            logging.error(f'Error bulk saving {object_type}: {e}', exc_info=True)
            self.session.rollback()
            raise


def import_zug_kub_data(
    session: Session,
    people_source: StrOrBytesPath,
    organizations_source: StrOrBytesPath,
    memberships_source: StrOrBytesPath,
) -> None:
    """Imports data from Zug KUB JSON sources."""

    people_data = _load_json(people_source)
    organization_data = _load_json(organizations_source)
    membership_data = _load_json(memberships_source)

    # Import people
    people_importer = PeopleImporter(session)
    parliamentarian_map = people_importer.bulk_import(people_data)

    # Import organizations
    organization_importer = OrganizationImporter(session)
    commission_map, parliamentary_group_map, party_map, other_organization_map = (
        organization_importer.bulk_import(organization_data)
    )

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
    membership_importer.bulk_import(membership_data)

    session.flush()
