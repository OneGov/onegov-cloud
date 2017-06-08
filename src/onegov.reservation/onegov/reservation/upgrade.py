""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from libres.db.models import Allocation, Reservation
from onegov.core.upgrade import upgrade_task
from onegov.reservation import LibresIntegration
from onegov.reservation import Resource
from sqlalchemy import Column, Text


def run_upgrades(context):
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
def add_form_definition_field(context):

    if run_upgrades(context):
        context.operations.add_column(
            'resources', Column('definition', Text, nullable=True)
        )


@upgrade_task('Add resource group field')
def add_resource_group_field(context):

    if run_upgrades(context):
        context.operations.add_column(
            'resources', Column('group', Text, nullable=True)
        )


@upgrade_task('Add reservations/allocations type field')
def add_reservations_allocations_type_field(context):

    if run_upgrades(context):
        context.operations.add_column(
            'reservations', Column('type', Text, nullable=True)
        )
        context.operations.add_column(
            'allocations', Column('type', Text, nullable=True)
        )


@upgrade_task('Make reservations/allocations payable')
def make_reservations_allocations_payable(context):

    if run_upgrades(context):
        for reservation in context.session.query(Reservation):
            reservation.type = 'custom'

        for allocation in context.session.query(Allocation):
            allocation.type = 'custom'


@upgrade_task('Set defaults on existing resources')
def set_defaults_on_existing_reservation_resourcd_objects(context):

    if run_upgrades(context):
        for resource in context.session.query(Resource):
            resource.payment_method = 'manual'
            resource.pricing_method = 'free'
            resource.price_per_hour = 0
            resource.price_per_item = 0
            resource.currency = 'CHF'
