""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

from libres.db.models import Allocation, Reservation
from libres.db.models.types.json_type import JSON
from onegov.core.upgrade import upgrade_task
from onegov.form.parser import ParsedForm
from onegov.form.orm_types import Formcode
from onegov.reservation import LibresIntegration
from onegov.reservation import Resource
from sqlalchemy import (
    bindparam, text, Column, Enum, ForeignKey, Integer, Text, UUID)


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.upgrade import UpgradeContext


def run_upgrades(context: UpgradeContext) -> bool:
    """ onegov.reservation is a bit special because it defines its tables
    through its own declarative base. This is due to libres requireing its own
    base.

    As a consequence, not all applications loaded in the current process have
    all the tables for all the modules (which is usually the case for all
    onegov modules using the default onegov.core.orm.Base class).

    This means we can only run the upgrades if Libres is integrated with
    the current app.

    """
    return isinstance(context.app, LibresIntegration)


@upgrade_task('Add form definition field')
def add_form_definition_field(context: UpgradeContext) -> None:

    if run_upgrades(context):
        context.operations.add_column(
            'resources', Column('definition', Text, nullable=True)
        )


@upgrade_task('Add resource group field')
def add_resource_group_field(context: UpgradeContext) -> None:

    if run_upgrades(context):
        context.operations.add_column(
            'resources', Column('group', Text, nullable=True)
        )


@upgrade_task('Add reservations/allocations type field')
def add_reservations_allocations_type_field(context: UpgradeContext) -> None:

    if run_upgrades(context):
        context.operations.add_column(
            'reservations', Column('type', Text, nullable=True)
        )
        context.operations.add_column(
            'allocations', Column('type', Text, nullable=True)
        )


@upgrade_task('Make reservations/allocations payable')
def make_reservations_allocations_payable(context: UpgradeContext) -> None:

    if run_upgrades(context):
        for reservation in context.session.query(Reservation):
            reservation.type = 'custom'

        for allocation in context.session.query(Allocation):
            allocation.type = 'custom'


@upgrade_task('Set defaults on existing resources')
def set_defaults_on_existing_reservation_resourcd_objects(
    context: UpgradeContext
) -> None:

    if run_upgrades(context):
        for resource in context.session.query(Resource):
            resource.payment_method = 'manual'
            resource.pricing_method = 'free'
            resource.price_per_hour = 0
            resource.price_per_item = 0
            resource.currency = 'CHF'


@upgrade_task('Add access_token to existing resources')
def add_access_token_to_existing_resources(context: UpgradeContext) -> None:

    if run_upgrades(context):
        for resource in context.session.query(Resource):
            resource.renew_access_token()


@upgrade_task('Add default view to existing resource types')
def add_default_view_to_existing_resource_types(
    context: UpgradeContext
) -> None:
    if run_upgrades(context):
        for resource in context.session.query(Resource):
            if resource.type == 'daypass':
                resource.default_view = 'month'
            else:
                resource.default_view = 'agendaWeek'


@upgrade_task('Make resource polymorphic type non-nullable')
def make_resource_polymorphic_type_non_nullable(
    context: UpgradeContext
) -> None:
    if context.has_table('reservations'):
        context.operations.execute(text("""
            UPDATE resources SET type = 'generic' WHERE type IS NULL;
        """))

        context.operations.alter_column('resources', 'type', nullable=False)


@upgrade_task('Add resource subgroup column (fixed)')
def add_resource_subgroup_column(context: UpgradeContext) -> None:
    if (
        context.has_table('resources')
        and not context.has_column('resources', 'subgroup')
    ):
        context.operations.add_column(
            'resources', Column('subgroup', Text, nullable=True)
        )


@upgrade_task('Migrate old text-based JSON columns to JSONB')
def migrated_text_based_json_to_jsonb(context: UpgradeContext) -> None:
    if context.has_table('reservations'):
        context.operations.alter_column(
            'reservations',
            'data',
            type_=JSON,
            postgresql_using='"data"::jsonb'
        )
    if context.has_table('allocations'):
        context.operations.alter_column(
            'allocations',
            'data',
            type_=JSON,
            postgresql_using='"data"::jsonb'
        )


@upgrade_task('Translate default views to their new names')
def translate_default_views_to_their_new_names(
    context: UpgradeContext
) -> None:
    if context.has_table('resources'):
        context.operations.execute(text("""
            UPDATE resources SET content = jsonb_set(
                content, '{default_view}', '"dayGridMonth"'
            ) WHERE content->>'default_view' = 'month';
        """))
        context.operations.execute(text("""
            UPDATE resources SET content = jsonb_set(
                content, '{default_view}', '"timeGridWeek"'
            ) WHERE content->>'default_view' = 'agendaWeek';
        """))


@upgrade_task('Add source_type column to reserved_slots')
def add_source_type_column_to_reserved_slots(context: UpgradeContext) -> None:
    if (
        context.has_table('reserved_slots')
        and not context.has_column('reserved_slots', 'source_type')
    ):
        context.operations.add_column(
          'reserved_slots',
          Column(
            'source_type',
            Enum(
                'reservation', 'blocker',
                name='reserved_slot_source_type'
            ),
            nullable=False,
            server_default='reservation'
          )
        )
        context.operations.alter_column(
          'reserved_slots',
          'source_type',
          server_default=None
        )


@upgrade_task('Make Reservation/Allocation.type not nullable')
def make_allocation_and_reservation_type_not_nullable(
    context: UpgradeContext
) -> None:
    if (
        context.has_table('allocations')
        and context.has_column('allocations', 'type')
    ):
        context.operations.execute(text("""
            UPDATE allocations
               SET type = 'generic'
             WHERE type IS NULL;
        """))
        context.operations.alter_column('allocations', 'type', nullable=False)
    if (
        context.has_table('reservations')
        and context.has_column('reservations', 'type')
    ):
        context.operations.execute(text("""
            UPDATE reservations
               SET type = 'generic'
             WHERE type IS NULL;
        """))
        context.operations.alter_column('reservations', 'type', nullable=False)


@upgrade_task('Add resource parent_id column')
def add_resource_parent_id_column(context: UpgradeContext) -> None:
    if (
        context.has_table('resources')
        and not context.has_column('resources', 'parent_id')
    ):
        context.operations.add_column(
            'resources',
            Column(
                'parent_id',
                UUID(as_uuid=True),
                ForeignKey('resources.id', ondelete='SET NULL'),
                nullable=True
            )
        )


@upgrade_task('Add additional indeces to reserved_slots')
def add_reserved_slots_indeces(context: UpgradeContext) -> None:
    context.operations.create_index(
        'ix_reserved_slots_source_type',
        'reserved_slots',
        columns=['source_type'],
        if_not_exists=True
    )
    context.operations.create_index(
        'start_end_tsrange_ix',
        'reserved_slots',
        columns=[text('tsrange(start, "end")')],
        postgresql_using='gist',
        if_not_exists=True
    )


@upgrade_task('Add additional indexes to libres tables')
def add_additional_indexes_to_libres_tables(context: UpgradeContext) -> None:
    context.operations.create_index(
        'ix_reserved_slots_end',
        'reserved_slots',
        columns=['end'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reserved_slots_allocation_id',
        'reserved_slots',
        columns=['allocation_id'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_token',
        'reservations',
        columns=['token'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_target',
        'reservations',
        columns=['target'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_target_type',
        'reservations',
        columns=['target_type'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_type',
        'reservations',
        columns=['type'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_resource',
        'reservations',
        columns=['resource'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_start',
        'reservations',
        columns=['start'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_end',
        'reservations',
        columns=['end'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_status',
        'reservations',
        columns=['status'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_email',
        'reservations',
        columns=['email'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservations_session_id',
        'reservations',
        columns=['session_id'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservation_blockers_token',
        'reservation_blockers',
        columns=['token'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservation_blockers_target',
        'reservation_blockers',
        columns=['target'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservation_blockers_target_type',
        'reservation_blockers',
        columns=['target_type'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservation_blockers_resource',
        'reservation_blockers',
        columns=['resource'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservation_blockers_start',
        'reservation_blockers',
        columns=['start'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_reservation_blockers_end',
        'reservation_blockers',
        columns=['end'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_allocations_resource',
        'allocations',
        columns=['resource'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_allocations_type',
        'allocations',
        columns=['type'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_allocations_mirror_of',
        'allocations',
        columns=['mirror_of'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_allocations_group',
        'allocations',
        columns=['group'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_allocations_start',
        'allocations',
        columns=['_start'],
        if_not_exists=True
    )
    context.operations.create_index(
        'ix_allocations_end',
        'allocations',
        columns=['_end'],
        if_not_exists=True
    )


@upgrade_task('Switch to JSON serialized custom resource form definitions')
def resources_switch_to_parsed_form(context: UpgradeContext) -> None:
    if not context.has_table('resources'):
        return

    # no migration needed, the old column is already gone
    if not context.has_column('resources', 'definition'):
        return

    # first add the new column
    context.operations.add_column(
        'resources',
        Column('parsed', Formcode, nullable=True)
    )

    # bulk update the table with the parsed definitions
    if values := [
        {
            'id': directory_id,
            'parsed': ParsedForm.from_formcode(definition),
        }
        for directory_id, definition in context.session.execute(text("""
            SELECT id, definition
              FROM resources
             WHERE definition IS NOT NULL
               AND definition != ''
        """))
    ]:
        context.session.execute(text("""
            UPDATE resources
               SET parsed = :parsed
             WHERE id = :id
        """).bindparams(
            bindparam('id', type_=UUID),
            bindparam('parsed', type_=Formcode)
        ), values)

    # finally remove the old column
    context.operations.drop_column('resources', 'definition')


def backfill_reserved_slot_source_ids(session: Any) -> None:
    """ Sets ``source_id`` on every reserved slot to the id of its owning
    reservation/blocker, and deletes slots that belong to no object (orphans
    left behind when a reservation/blocker was deleted without its slots).

    On partly_available allocations the slot falls within the owner's range;
    otherwise (whole allocation, or group owners without a range) the
    allocation group identifies the owner.
    """
    for source_type, table in (
        ('reservation', 'reservations'),
        ('blocker', 'reservation_blockers'),
    ):
        session.execute(text(
            'UPDATE reserved_slots rs SET source_id = ('
            f'  SELECT o.id FROM {table} o'
            '   JOIN allocations a ON a.id = rs.allocation_id'
            '  WHERE o.token = rs.reservation_token'
            '    AND o.target = a."group"'
            '    AND (o.start IS NULL OR a.partly_available = false'
            '         OR (rs.start >= o.start AND rs."end" <= o."end"))'
            '  ORDER BY o.id LIMIT 1'
            ') '
            f"WHERE rs.source_type = '{source_type}' "
            'AND rs.source_id IS NULL'
        ))

    session.execute(
        text('DELETE FROM reserved_slots WHERE source_id IS NULL')
    )


@upgrade_task('Add source_id to reserved slots')
def add_source_id_to_reserved_slots(context: UpgradeContext) -> None:
    """ Records the owning reservation/blocker id on each reserved slot so a
    slot can be attributed to its exact object directly, instead of inferring
    it from the allocation and time range. Slots that belong to no object are
    orphans (their reservation/blocker was already deleted) and are removed.
    """

    if not run_upgrades(context):
        return

    if context.has_column('reserved_slots', 'source_id'):
        return

    context.operations.add_column(
        'reserved_slots', Column('source_id', Integer, nullable=True)
    )

    backfill_reserved_slot_source_ids(context.session)

    # every remaining slot now has an owner, so enforce it
    context.operations.alter_column(
        'reserved_slots', 'source_id', nullable=False
    )

    context.operations.create_index(
        'ix_reserved_slots_source_id', 'reserved_slots', ['source_id']
    )
@upgrade_task('Store pricing settings on reservations')
def store_pricing_settings_on_reservations(context: UpgradeContext) -> None:
    if not context.has_table('resources'):
        return

    context.session.execute(text("""
        WITH adata AS (
            SELECT "group",
                   jsonb_build_object(
                        'pricing_method',
                        data->'pricing_method',
                        'price_per_hour',
                        COALESCE(data->'price_per_hour', '0.0'::jsonb),
                        'price_per_item',
                        COALESCE(data->'price_per_item', '0.0'::jsonb),
                        'currency',
                        COALESCE(data->'currency', '"CHF"'::jsonb)
                   ) AS pricing
              FROM allocations
             WHERE resource = mirror_of
               AND data->>'pricing_method' = 'price_per_item'
                OR data->>'pricing_method' = 'price_per_hour'
                OR data->>'pricing_method' = 'free'
        )
        UPDATE reservations
           SET data = COALESCE(data, '{}'::jsonb) ||
              CASE
                WHEN EXISTS (SELECT 1 FROM adata WHERE adata."group" = target)
                THEN
                    (
                        SELECT pricing
                          FROM adata
                         WHERE adata."group" = target
                         LIMIT 1
                    ) || jsonb_build_object(
                        'cost_object',
                        resources.content->'cost_object'
                    )
                ELSE
                    jsonb_build_object(
                        'pricing_method',
                        resources.content->'pricing_method',
                        'price_per_hour',
                        COALESCE(
                            resources.content->'price_per_hour',
                            '0.0'::jsonb
                        ),
                        'price_per_item',
                        COALESCE(
                            resources.content->'price_per_item',
                            '0.0'::jsonb
                        ),
                        'currency',
                        resources.content->'currency',
                        'cost_object',
                        resources.content->'cost_object'
                    )
               END
           FROM resources
          WHERE resources.id = resource

    """))
