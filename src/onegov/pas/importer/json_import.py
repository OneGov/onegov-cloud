from __future__ import annotations

from sqlalchemy.orm import Session
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Self, Literal
from collections.abc import Sequence

from onegov.pas.models import Parliamentarian, ParliamentaryGroup, Commission
from onegov.pas.models.commission_membership import (
    ROLES as MEMBERSHIP_ROLES, CommissionMembership,
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
]  # Type hint for organization type
OrganizationData = dict[str, Any]


class InvalidDataError(Exception):
    pass


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


def load_json_data(source: str | Path | TextIO) -> dict[str, Any]:
    """Load JSON data from either a JSON string or a file path."""
    try:
        # If string starts with {, treat as JSON string
        if isinstance(source, str) and source.lstrip().startswith('{'):
            return json.loads(source)

        # Otherwise treat as file path
        if isinstance(source, (str, Path)):
            with open(source, encoding='utf-8') as f:
                return json.load(f)

        # Handle file-like objects
        return json.load(source)

    except Exception as e:
        raise InvalidDataError(f'Failed to load JSON data: {e!s}')


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
    """ Importer for Parliamentarian data from api/v2/people endpoint
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


# def determine_membership_role(membership_data: MembershipData) -> str:
#     """Determines the membership role based on organization type and role text."""
#     role_text = membership_data.get('role', '').lower()
#     org_type_title = membership_data.get('organization', {}).get(
#         'organizationTypeTitle'
#     )
#
#     if org_type_title == 'Kommission':
#         if 'präsident' in role_text:
#             return 'president'
#         elif 'vizepräsident' in role_text or 'vize-präsident' in role_text:
#             return 'vicepresident'
#         elif 'vote counter' in role_text:  # Adjust based on actual text
#             return 'votecounter'
#         else:
#             return 'member'  # Default for Kommission is member
#     elif org_type_title == 'Fraktion':  # Parliamentary Group Roles
#         if 'präsident' in role_text:
#             return 'president_parliamentary_group'  # Use specific parliamentary group president role
#         elif 'vizepräsident' in role_text or 'vize-präsident' in role_text:
#             return 'vicepresident'
#         elif 'vote counter' in role_text:  # Adjust based on actual text
#             return 'votecounter'
#         elif 'mediamanager' in role_text or 'media manager' in role_text:
#             return 'mediamanager'
#         else:
#             return 'member'  # Default for Fraktion is member
#     elif (
#             org_type_title == 'Kantonsrat'
#     ):  # Parliamentarian Roles (for Kantonsrat "memberships")
#         #  "Kantonsrat" memberships might represent the general role of being a parliamentarian.
#         #  You might need to adjust role determination based on your specific needs.
#         return 'member'  # Default Kantonsrat role is member
#     elif org_type_title == 'Sonstige':
#         return 'member'  # Default role for "Sonstige"
#     else:
#         return 'none'  # Default to 'none' if type is unknown


class MembershipImporter(DataImporter):
    """Importer for CommissionMembership data."""

    membership_attribute_map: dict[str, str] = {
        'start': 'start',
        'end': 'end',
        # role is handled separately
    }

    def init(
        self,
        session: Session,
        parliamentarian_map: dict[str, Parliamentarian],
        commission_map: dict[str, Commission],
        parliamentary_group_map: dict[
            str, ParliamentaryGroup
        ],  # Add parliamentary group map
        other_organization_map: dict[
            str, Any
        ],  # Add other org map if needed
    ) -> None:
        super().init(session)
        self.parliamentarian_map = parliamentarian_map
        self.commission_map = commission_map
        self.parliamentary_group_map = (
            parliamentary_group_map  # Store parliamentary group map
        )
        self.other_organization_map = (
            other_organization_map  # Store other org map if needed
        )

    def bulk_import(
        self, memberships_data: Sequence[MembershipData]
    ) -> None:
        """Imports commission memberships from JSON data."""
        commission_memberships = []

        for membership in memberships_data:
            try:
                person_id = membership['person']['id']
                org_id = membership['organization']['id']

                parliamentarian = self.parliamentarian_map.get(person_id)
                if not parliamentarian:
                    logging.warning(
                        f'Skipping membership: Parliamentarian with id {person_id} not found.'
                    )
                    continue

                organization_data = membership['organization']
                org_type_title = organization_data.get(
                    'organizationTypeTitle'
                )

                organization = None
                if org_type_title == 'Kommission':
                    organization = self.commission_map.get(org_id)
                elif org_type_title == 'Fraktion':
                    organization = self.parliamentary_group_map.get(org_id)
                elif (
                        org_type_title == 'Kantonsrat'
                        or org_type_title == 'Sonstige'
                ):
                    organization = self.other_organization_map.get(
                        org_id
                    )  # Or handle Kantonsrat differently if needed
                else:
                    logging.warning(
                        f'Skipping membership: Unknown organization type {org_type_title} for org id {org_id}'
                    )
                    continue

                if not organization:
                    logging.warning(
                        f'Skipping membership: Organization of type {org_type_title} with id {org_id} not found.'
                    )
                    continue

                membership_kwargs = {}
                membership_kwargs['parliamentarian'] = parliamentarian
                membership_kwargs['organization'] = (
                    organization  # Polymorphic relationship
                )

                for (
                        json_key,
                        model_attr,
                ) in self.membership_attribute_map.items():
                    membership_kwargs[model_attr] = self.parse_date(
                        membership.get(json_key)
                    )

                membership_kwargs['role'] = determine_membership_role(
                    membership
                )  # Determine role dynamically

                commission_membership = CommissionMembership(
                    **membership_kwargs
                )  # Assuming CommissionMembership is the base class for all memberships
                commission_memberships.append(commission_membership)

            except Exception as e:
                logging.error(
                    f'Error creating membership for person_id {membership.get("person", {}).get("id")}, org_id {membership.get("organization", {}).get("id")}: {e}',
                    exc_info=True,
                )

        self._bulk_save(commission_memberships, 'commission memberships')


class OrganizationImporter(DataImporter):
    """Importer for Organization data from organizations.json."""

    organization_attribute_map: dict[str, str] = {
        'name': 'name',
        'description': 'description',
        'isActive': 'is_active',  # Assuming you have an is_active field in your models
        # ... other common fields ...
    }

    def bulk_import(
        self, organizations_data: Sequence[OrganizationData]
    ) -> tuple[
        dict[str, Commission],
        dict[str, ParliamentaryGroup],
        dict[str, Any],
    ]:  # Return maps for different org types
        """Imports organizations from JSON and returns maps for commissions
        and parliamentary groups."""
        commissions = []
        parliamentary_groups = []
        other_organizations = []  # For "Sonstige" or other types

        commission_map: dict[str, Commission] = {}
        parliamentary_group_map: dict[str, ParliamentaryGroup] = {}
        other_organization_map: dict[str, Any] = (
            {}
        )  # Adjust type as needed

        for org_data in organizations_data:
            breakpoint()
            try:
                org_type_title = org_data.get('organizationTypeTitle')

                if org_type_title == 'Kommission':
                    commission = self._create_commission(org_data)
                    if commission:
                        commissions.append(commission)
                        commission_map[org_data['id']] = commission
                elif org_type_title == 'Fraktion':
                    parliamentary_group = self._create_parliamentary_group(
                        org_data
                    )
                    if parliamentary_group:
                        parliamentary_groups.append(parliamentary_group)
                        parliamentary_group_map[org_data['id']] = (
                            parliamentary_group
                        )
                elif org_type_title == 'Kantonsrat':
                    # Handle Kantonsrat as ParliamentarianRole
                    kantonsrat_role = self._handle_kantonsrat(
                        org_data
                    )  # Example handling
                    if kantonsrat_role:
                        other_organizations.append(
                            kantonsrat_role
                        )  # Adjust list as needed
                        other_organization_map[org_data['id']] = (
                            kantonsrat_role  # Adjust map as needed
                        )
                elif org_type_title == 'Sonstige':
                    other_org = self._create_other_organization(
                        org_data
                    )  # Placeholder for "Sonstige"
                    if other_org:
                        other_organizations.append(other_org)
                        other_organization_map[org_data['id']] = other_org
                else:
                    logging.warning(
                        f"Unknown organization type: {org_type_title} for org id {org_data.get('id')}"
                    )

            except Exception as e:
                logging.error(
                    f'Error importing organization with id {org_data.get("id")}: {e}',
                    exc_info=True,
                )

        self._bulk_save(commissions, 'commissions')
        self._bulk_save(parliamentary_groups, 'parliamentary groups')
        self._bulk_save(
            other_organizations, 'other organizations'
        )  # Save other orgs if needed

        return (
            commission_map,
            parliamentary_group_map,
            other_organization_map,
        )  # Return all maps

    def _create_commission(
        self, org_data: OrganizationData
    ) -> Commission | None:
        """Creates a Commission object."""
        if not org_data.get('id'):
            logging.warning(
                f"Skipping commission due to missing ID: {org_data.get('name')}"
            )
            return None

        commission_kwargs = {}
        for (
                json_key,
                model_attr,
        ) in self.organization_attribute_map.items():
            commission_kwargs[model_attr] = org_data.get(json_key)

        commission_kwargs['type'] = (
            'official'  # Assuming "Kommission" maps to 'official' type
        )
        commission = Commission(**commission_kwargs)
        return commission

    def _create_parliamentary_group(
        self, org_data: OrganizationData
    ) -> ParliamentaryGroup | None:
        """Creates a ParliamentaryGroup object."""
        if not org_data.get('id'):
            logging.warning(
                f"Skipping parliamentary group due to missing ID: {org_data.get('name')}"
            )
            return None

        parliamentary_group_kwargs = {}
        for (
                json_key,
                model_attr,
        ) in self.organization_attribute_map.items():
            parliamentary_group_kwargs[model_attr] = org_data.get(json_key)

        parliamentary_group = ParliamentaryGroup(
            **parliamentary_group_kwargs
        )
        return parliamentary_group

    def _handle_kantonsrat(
        self, org_data: OrganizationData
    ) -> Any:  # Adjust return type as needed
        """Handles "Kantonsrat" organization type.  This might create a ParliamentarianRole or something else."""
        #  This is where you decide how to represent "Kantonsrat".
        #  If it's just a ParliamentarianRole, you might create that directly.
        #  If it's a special Organization type, create that.

        logging.info(f"Handling Kantonsrat: {org_data.get('name')}")
        breakpoint()
        # Example:  If Kantonsrat is just a role, you might not create an Organization object at all.
        # Instead, you might use it to set a default ParliamentarianRole for members.
        # For now, let's just return None as a placeholder.
        return None  # Placeholder - adjust based on your model

    def _create_other_organization(
        self, org_data: OrganizationData
    ) -> Any:  # Adjust return type as needed
        """Creates a placeholder for "Sonstige" organization types."""
        logging.info(
            f"Creating 'Sonstige' organization: {org_data.get('name')}"
        )
        # You might create a generic Organization model here, or skip
        # "Sonstige" types if not needed.
        return None  # Placeholder - adjust based on your model


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

    people_importer = PeopleImporter(session)
    parliamentarian_map = people_importer.bulk_import(people_data)

    organization_importer = OrganizationImporter(session)
    commission_map, parliamentary_group_map, other_organization_map = (
        organization_importer.bulk_import(organization_data)
    )

    membership_importer = MembershipImporter(session)
    membership_importer.init(
        session,
        parliamentarian_map,
        commission_map,
        parliamentary_group_map,
        other_organization_map,
    )
    membership_importer.bulk_import(membership_data)

    session.flush()
