from __future__ import annotations

from onegov.pas.log import log
from onegov.pas.models import ImportLog


from typing import TYPE_CHECKING, Any, cast
if TYPE_CHECKING:
    import logging
    from uuid import UUID
    from collections.abc import Sequence
    from sqlalchemy.orm import Session
    from onegov.pas.importer.json_import import (
        ImportCategoryResult,
        PersonData,
        OrganizationData,
        MembershipData,
    )


def _serialize_model_objects(obj_list: list[Any]) -> list[dict[str, Any]]:
    """Convert model objects to JSON-serializable dictionaries."""
    serialized = []
    for obj in obj_list:
        if hasattr(obj, '__tablename__'):
            # SQLAlchemy model object
            result = {
                'id': str(obj.id) if obj.id else None,
                'type': obj.__class__.__name__,
            }
            # Add identifying fields based on model type
            if hasattr(obj, 'last_name') and hasattr(obj, 'first_name'):
                result.update({
                    'last_name': obj.last_name,
                    'first_name': obj.first_name,
                    'email': getattr(obj, 'email', None)
                })
            elif hasattr(obj, 'name'):
                result['name'] = obj.name
            elif hasattr(obj, 'title'):
                result['title'] = obj.title
            serialized.append(result)
        else:
            # For non-model objects, keep as-is
            serialized.append(obj)
    return serialized


def import_zug_kub_data(
    session: Session,
    people_data: Sequence[PersonData],
    organization_data: Sequence[OrganizationData],
    membership_data: Sequence[MembershipData],
    user_id: UUID | None = None,
    import_type: str = 'cli',
    logger: logging.Logger | None = None,
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
        logger: Optional logger to use instead of module logger

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

    # Use provided logger or default to module logger
    if logger is None:
        logger = log

    try:
        # Use a savepoint; rollback occurs automatically on exception
        with session.begin_nested():
            people_importer = PeopleImporter(session, logger)
            (parliamentarian_map, people_details, people_processed) = (
                people_importer.bulk_import(people_data)
            )
            import_details['parliamentarians'] = {
                'created': _serialize_model_objects(people_details['created']),
                'updated': _serialize_model_objects(people_details['updated']),
                'processed': people_processed,
            }

            organization_importer = OrganizationImporter(session, logger)
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
                    created_objs = details_list_dict.get('created', [])
                    updated_objs = details_list_dict.get('updated', [])
                    import_details[category] = {
                        'created': _serialize_model_objects(created_objs),
                        'updated': _serialize_model_objects(updated_objs),
                        'processed': processed_count,
                    }

            # Add 'other' processed count to log_details separately
            log_details['other_organizations_processed'] = (
                org_processed_counts.get('other', 0)
            )
            log_details['parliamentary_groups_processed'] = (
                org_processed_counts.get('parliamentary_groups', 0)
            )

            membership_importer = MembershipImporter(session, logger)
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
                        created_parl = details_dict.get('created', [])
                        updated_parl = details_dict.get('updated', [])
                        import_details['parliamentarians']['created'].extend(
                            _serialize_model_objects(created_parl)
                        )
                        import_details['parliamentarians']['updated'].extend(
                            _serialize_model_objects(updated_parl)
                        )

                elif category in (
                    'commission_memberships',
                    'parliamentarian_roles',
                ):
                    created_items = details_dict.get('created', [])
                    updated_items = details_dict.get('updated', [])
                    import_details[category] = cast(
                        'ImportCategoryResult', {
                            'created': _serialize_model_objects(created_items),
                            'updated': _serialize_model_objects(updated_items),
                            'processed': details_dict.get('processed', 0)
                        }
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
            logger.info(
                'KUB data import processing successful within transaction.'
            )
    except Exception as e:
        final_error = e
        log_status = 'failed'
        log_details['error'] = str(e)
        logger.exception('KUB data import failed')

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
            logger.info(
                f'KUB data import attempt logged with status: {log_status}'
            )
        except Exception:
            logger.exception(
                'Failed to log import status'
            )

        if final_error:
            raise RuntimeError('KUB data import failed.') from final_error

    return import_details
