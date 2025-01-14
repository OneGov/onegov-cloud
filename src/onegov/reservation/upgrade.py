""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

from libres.db.models import Allocation, Reservation
from onegov.core.upgrade import upgrade_task
from onegov.reservation import LibresIntegration
from onegov.reservation import Resource
from sqlalchemy import Column, Text


from typing import TYPE_CHECKING
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
        context.operations.execute("""
            UPDATE resources SET type = 'generic' WHERE type IS NULL;
        """)

        context.operations.alter_column('resources', 'type', nullable=False)
