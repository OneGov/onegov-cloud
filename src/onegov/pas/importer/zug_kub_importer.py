from __future__ import annotations

from onegov.pas import log
from onegov.pas.models import ImportLog


from typing import TYPE_CHECKING, Any, cast
if TYPE_CHECKING:
    from uuid import UUID
    from collections.abc import Sequence
    from sqlalchemy.orm import Session
    from onegov.pas.importer.json_import import (
        ImportCategoryResult,
        PersonData,
        OrganizationData,
        MembershipData,
    )


def import_zug_kub_data(
    session: Session,
    people_data: Sequence[PersonData],
    organization_data: Sequence[OrganizationData],
    membership_data: Sequence[MembershipData],
    user_id: UUID | None = None,
    import_type: str = 'cli',
) -> dict[str, ImportCategoryResult]:
    """
    Imports data from KUB JSON files within a single transaction,
    logs the outcome, and returns details of changes including processed
    counts.

    Args:
        session: Database session
        people_data: People data to import
        organization_data: Organization data to import
        membership_data: Membership data to import
        user_id: ID of user performing the import (optional)
        import_type: Type of import ('cli', 'upload', or 'automatic')

    Returns a dictionary where keys are categories (e.g., 'parliamentarians')
    and values are dictionaries containing 'created' (list), 'updated' (list),
    and 'processed' (int).

    Rolls back changes within this import if an internal error occurs.
    Logs the attempt regardless of success or failure.
    """
    from onegov.pas.importer.json_import import (
        PeopleImporter,
        OrganizationImporter,
        MembershipImporter,
    )

    import_details: dict[str, ImportCategoryResult] = {}
    log_status = 'failed'
    log_details: dict[str, Any] = {}
    final_error: Exception | None = None

    try:
        # Use a savepoint; rollback occurs automatically on exception
        with session.begin_nested():
            people_importer = PeopleImporter(session)
            (parliamentarian_map, people_details, people_processed) = (
                people_importer.bulk_import(people_data)
            )
            import_details['parliamentarians'] = {
                'created': people_details['created'],
                'updated': people_details['updated'],
                'processed': people_processed,
            }

            organization_importer = OrganizationImporter(session)
            (
                commission_map,
                parliamentary_group_map,
                party_map,
                other_organization_map,
                org_details,
                org_processed_counts,
            ) = organization_importer.bulk_import(organization_data)

            for category, details_list_dict in org_details.items():
                processed_count = org_processed_counts.get(category, 0)
                # Only add categories that have actual ORM objects
                # (Commissions, Parties)
                if category in ('commissions', 'parties'):
                    import_details[category] = {
                        'created': details_list_dict.get('created', []),
                        'updated': details_list_dict.get('updated', []),
                        'processed': processed_count,
                    }

            # Add 'other' processed count to log_details separately
            log_details['other_organizations_processed'] = (
                org_processed_counts.get('other', 0)
            )
            log_details['parliamentary_groups_processed'] = (
                org_processed_counts.get('parliamentary_groups', 0)
            )

            membership_importer = MembershipImporter(session)
            membership_importer.init(
                session,
                parliamentarian_map,
                commission_map,
                parliamentary_group_map,
                party_map,
                other_organization_map,
            )
            (membership_details, membership_processed_counts) = (
                membership_importer.bulk_import(membership_data)
            )

            for category, details_dict in membership_details.items():
                if category == 'parliamentarians_from_memberships':
                    if isinstance(
                        details_dict, dict
                    ):
                        import_details['parliamentarians']['created'].extend(
                            details_dict.get('created', [])
                        )
                        import_details['parliamentarians']['updated'].extend(
                            details_dict.get('updated', [])
                        )

                elif category in (
                    'commission_memberships',
                    'parliamentarian_roles',
                ):
                    import_details[category] = cast(
                        'ImportCategoryResult', details_dict
                    )

            log_details['skipped_memberships'] = (
                membership_processed_counts.get('skipped', 0)
            )

            log_details['summary'] = {}
            for k, v in import_details.items():
                # v is now guaranteed to be ImportCategoryResult
                log_details['summary'][k] = {
                    'created_count': len(v['created']),
                    'updated_count': len(v['updated']),
                    'processed_count': v['processed'],
                }
            log_details['summary']['other_organizations_processed'] = (
                log_details['other_organizations_processed']
            )
            log_details['summary']['parliamentary_groups_processed'] = (
                log_details['parliamentary_groups_processed']
            )
            log_details['summary']['skipped_memberships'] = log_details[
                'skipped_memberships'
            ]

            log_status = 'completed'
            log.info(
                'KUB data import processing successful within transaction.'
            )
    except Exception as e:
        final_error = e
        log_status = 'failed'
        log_details['error'] = str(e)
        log.error(f'KUB data import failed: {e}', exc_info=True)

    finally:
        try:
            import_log = ImportLog(
                user_id=user_id,
                details=log_details,
                status=log_status,
                import_type=import_type
            )
            session.add(import_log)
            if session.is_active:
                session.flush()
            log.info(
                f'KUB data import attempt logged with status: {log_status}'
            )
        except Exception as log_e:
            log.error(
                f'Failed to log import status: {log_e}', exc_info=True
            )

        if final_error:
            raise RuntimeError('KUB data import failed.') from final_error

    return import_details
