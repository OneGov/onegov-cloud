from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, Sequence, TextIO

from sqlalchemy.orm import Session

from onegov.pas.models import (
    Parliamentarian,
    Commission,
    CommissionMembership,
)
from onegov.pas.models.commission_membership import (
    ROLES as MEMBERSHIP_ROLES,
)


# Type definitions with modern syntax (already good)
class EmailData(TypedDict):
    id: str
    email: str
    isDefault: bool


class PersonData(TypedDict):
    id: str
    firstName: str
    officialName: str
    salutation: str | None
    primaryEmail: EmailData | None
    created: str
    modified: str
    isActive: bool


class OrganizationData(TypedDict):
    id: str
    name: str
    description: str
    organizationTypeTitle: str
    created: str
    modified: str
    isActive: bool


class MembershipData(TypedDict):
    id: str
    person: dict[str, Any]
    organization: dict[str, Any]
    start: str | None
    end: str | None
    role: str | None  # Add role to MembershipData for clarity


class InvalidDataError(Exception):  # Define InvalidDataError
    pass


def parse_date(
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


def determine_commission_type(name: str) -> str:
    name_lower = name.lower()
    if 'interkantonale' in name_lower:
        return 'intercantonal'
    if 'amtliche' in name_lower:
        return 'official'
    return 'normal'


def determine_membership_role(membership_data: dict[str, Any]) -> str:
    role = membership_data.get('role', '').lower()
    role_mappings = {
        k: k for k in MEMBERSHIP_ROLES.keys()
    }  # Use enum keys directly
    return role_mappings.get(role, 'member')


def load_json_data(source: str | Path | TextIO) -> dict[str, Any]:
    """Load JSON data from either a JSON string or a file path."""
    try:
        # If string starts with {, treat as JSON string
        if isinstance(source, str) and source.lstrip().startswith('{'):
            return json.loads(source)

        # Otherwise treat as file path
        if isinstance(source, (str, Path)):
            with open(source, 'r', encoding='utf-8') as f:
                return json.load(f)

        # Handle file-like objects
        return json.load(source)

    except Exception as e:
        raise InvalidDataError(f'Failed to load JSON data: {str(e)}')


class DataImporter:
    """Base class for all importers with common functionality."""

    def __init__(self, session: Session) -> None:
        self.session = session

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


class ParliamentarianImporter(DataImporter):
    """Importer for Parliamentarian data."""

    person_attribute_map: dict[str, str] = {  # Define attribute map
        'firstName': 'first_name',
        'officialName': 'last_name',
        'salutation': 'salutation',
        # email_primary will be handled separately
        'created': 'created',
        'modified': 'modified',
    }

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.parliamentarian_map: dict[str, Parliamentarian] = {}

    def _validate_person_data(self, data: dict[str, Any]) -> bool:
        required_fields = {'id', 'firstName', 'officialName'}
        return all(data.get(field) for field in required_fields)

    def bulk_import(
        self, people_data: Sequence[PersonData]
    ) -> dict[str, Parliamentarian]:
        valid_people = [
            p for p in people_data if self._validate_person_data(p)
        ]
        parliamentarians = []

        for person in valid_people:
            try:
                parliamentarian_kwargs = {}

                for (
                    json_key,
                    model_attr,
                ) in (
                    self.person_attribute_map.items()
                ):  # Use attribute map
                    parliamentarian_kwargs[model_attr] = person.get(
                        json_key
                    )

                parliamentarian_kwargs['email_primary'] = person.get(
                    'primaryEmail', {}
                ).get(
                    'email'
                )  # Handle primary email

                parliamentarian_kwargs['created'] = parse_date(
                    person.get('created')
                )  # Parse dates
                parliamentarian_kwargs['modified'] = parse_date(
                    person.get('modified')
                )

                parliamentarian = Parliamentarian(
                    **parliamentarian_kwargs
                )  # Create Parliamentarian object
                parliamentarians.append(parliamentarian)
                self.parliamentarian_map[person['id']] = parliamentarian
            except Exception as e:
                logging.error(
                    f"Error creating parliamentarian for id {person.get('id')}: {e}",
                    exc_info=True,
                )

        self._bulk_save(parliamentarians, 'parliamentarians')
        return self.parliamentarian_map


class CommissionImporter(DataImporter):
    """Importer for Commission data."""

    organization_attribute_map: dict[str, str] = {  # Define attribute map
        'name': 'name',
        'description': 'description',
        'created': 'created',
        'modified': 'modified',
    }

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self.commission_map: dict[str, Commission] = {}

    def _validate_organization_data(self, data: dict[str, Any]) -> bool:
        return (
            bool(data.get('id'))
            and bool(data.get('name'))
            and data.get('organizationTypeTitle') == 'Kommission'
        )

    def bulk_import(
        self, organizations_data: Sequence[OrganizationData]
    ) -> dict[str, Commission]:
        valid_orgs = [
            org
            for org in organizations_data
            if self._validate_organization_data(org)
        ]

        commissions = []
        for org in valid_orgs:
            try:
                commission_kwargs = {}

                for (
                    json_key,
                    model_attr,
                ) in (
                    self.organization_attribute_map.items()
                ):  # Use attribute map
                    commission_kwargs[model_attr] = org.get(json_key)

                commission_kwargs['type'] = determine_commission_type(
                    org['name']
                )  # Determine commission type

                commission_kwargs['created'] = parse_date(
                    org.get('created')
                )  # Parse dates
                commission_kwargs['modified'] = parse_date(
                    org.get('modified')
                )

                commission = Commission(**commission_kwargs)
                commissions.append(commission)
                self.commission_map[org['id']] = commission
            except Exception as e:
                logging.error(
                    f"Error creating commission for id {org.get('id')}: {e}",
                    exc_info=True,
                )

        self._bulk_save(commissions, 'commissions')
        return self.commission_map


class MembershipImporter(DataImporter):
    """Importer for CommissionMembership data."""

    membership_attribute_map: dict[str, str] = {  # Define attribute map
        'start': 'start',
        'end': 'end',
        # role is handled separately
    }

    def __init__(
        self,
        session: Session,
        parliamentarian_map: dict[str, Parliamentarian],
        commission_map: dict[str, Commission],
    ) -> None:
        super().__init__(session)
        self.parliamentarian_map = parliamentarian_map
        self.commission_map = commission_map

    def _validate_membership_data(self, data: dict[str, Any]) -> bool:
        return bool(
            data.get('person', {}).get('id')
            and data.get('organization', {}).get('id')
        )

    def bulk_import(
        self, memberships_data: Sequence[MembershipData]
    ) -> None:
        valid_memberships = [
            m
            for m in memberships_data
            if self._validate_membership_data(m)
        ]

        commission_memberships = []
        for membership in valid_memberships:
            try:
                person_id = membership['person']['id']
                org_id = membership['organization']['id']

                parliamentarian = self.parliamentarian_map.get(person_id)
                commission = self.commission_map.get(org_id)

                if not parliamentarian or not commission:
                    logging.warning(
                        f"Skipping membership due to missing parliamentarian "
                        f"or commission. "
                        f"Person ID: {person_id}, Org ID: {org_id}"
                    )
                    continue

                membership_kwargs = {}
                membership_kwargs['parliamentarian'] = (
                    parliamentarian  # Relationships directly
                )
                membership_kwargs['commission'] = commission

                for (
                    json_key,
                    model_attr,
                ) in (
                    self.membership_attribute_map.items()
                ):  # Use attribute map
                    membership_kwargs[model_attr] = parse_date(
                        membership.get(json_key)
                    )  # Parse dates

                membership_kwargs['role'] = determine_membership_role(
                    membership
                )  # Determine role

                commission_membership = CommissionMembership(
                    **membership_kwargs
                )
                commission_memberships.append(commission_membership)
            except Exception as e:
                logging.error(
                    f'Error creating commission membership for person_id {membership.get("person", {}).get("id")}, org_id {membership.get("organization", {}).get("id")}: {e}',
                    exc_info=True,
                )

        self._bulk_save(commission_memberships, 'commission memberships')


def import_zug_kub_data(
    session: Session,
    people_source: str | Path | TextIO,
    organizations_source: str | Path | TextIO,
    memberships_source: str | Path | TextIO,
) -> None:
    """Import parliament data from 3 json files retrived of internal zug
    KuB api v2.

    Input: people.json, organizations.json, memberships.json
    """

    logging.info('Starting data import...')
    try:
        # Load data
        people_data = load_json_data(people_source)
        organizations_data = load_json_data(organizations_source)
        memberships_data = load_json_data(memberships_source)

        if not all([people_data, organizations_data, memberships_data]):
            raise InvalidDataError(
                'Failed to load all required data files'
            )

        # Import data in correct order
        parliamentarian_importer = ParliamentarianImporter(session)
        parliamentarian_map = parliamentarian_importer.bulk_import(
            people_data['results']
        )

        commission_importer = CommissionImporter(session)
        commission_map = commission_importer.bulk_import(
            organizations_data['results']
        )

        membership_importer = MembershipImporter(
            session, parliamentarian_map, commission_map
        )
        membership_importer.bulk_import(memberships_data['results'])

        session.flush()
        logging.info('Data import completed successfully')

    except InvalidDataError as e:
        session.rollback()
        logging.error(f'Data import failed due to invalid data: {e}')
        raise
    except Exception as e:
        session.rollback()
        logging.error(
            f'Fatal error during data import: {e}', exc_info=True
        )
        raise
