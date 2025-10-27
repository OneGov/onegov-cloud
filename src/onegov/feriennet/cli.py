from __future__ import annotations

import click

from onegov.core.cli import GroupContext, command_group, pass_group_context
from onegov.activity.models import BookingPeriod
from onegov.activity.models import Occasion
from sqlalchemy import text


from typing import TYPE_CHECKING

from onegov.core.utils import Bunch
from onegov.feriennet.upgrade import (UpgradeContext,
                                      migrate_homepage_structure_for_feriennet)
from onegov.town6.upgrade import migrate_theme_options
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.feriennet.app import FeriennetApp
    from onegov.feriennet.request import FeriennetRequest


cli = command_group()


@cli.command(name='delete-period', context_settings={'singular': True})
@click.argument('title')
def delete_period(
    title: str
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """ Deletes all the data associated with a period, including:

    * Payments
    * Bookings
    * Occasions
    * Publication Requests
    * Tickets

    We usually don't allow for this, but there tends to be a request here and
    there about this, where a Ferienpass created a period for testing and
    tries to return to a semi-clean state.

    Example::

        onegov-feriennet --select /foo/bar delete-period "Ferienpass Test"

    """

    def delete_period(
        request: FeriennetRequest,
        app: FeriennetApp
    ) -> None:

        period = request.session.query(
            BookingPeriod).filter_by(title=title).first()

        if not period:
            raise click.ClickException(f'Could not find period «{title}»')

        request.session.execute(text("""
            DELETE FROM payments WHERE payments.id IN (
                SELECT payment_id FROM payments_for_invoice_items_payments
                WHERE invoice_items_id IN (
                    SELECT id FROM invoice_items
                    WHERE invoice_id IN (
                        SELECT id FROM invoices WHERE period_id = :period
                    )
                )
            )
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM payments_for_invoice_items_payments
            WHERE invoice_items_id IN (
                SELECT id FROM invoice_items
                WHERE invoice_id IN (
                    SELECT id FROM invoices WHERE period_id = :period
                )
            )
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM invoice_items where invoice_id IN (
                SELECT id FROM invoices WHERE period_id = :period
            )
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM invoice_references where invoice_id IN (
                SELECT id FROM invoices WHERE period_id = :period
            )
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM invoices WHERE period_id = :period
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM tickets WHERE handler_id::uuid IN (
                SELECT id FROM publication_requests
                WHERE period_id = :period
            )
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM publication_requests WHERE period_id = :period
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM bookings WHERE period_id = :period
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM occasion_dates WHERE occasion_id IN (
                SELECT id FROM occasions WHERE period_id = :period
            )
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM occasion_needs WHERE occasion_id IN (
                SELECT id FROM occasions WHERE period_id = :period
            )
        """), {
            'period': period.id
        })

        request.session.execute(text("""
            DELETE FROM occasions WHERE period_id = :period
        """), {
            'period': period.id
        })

        # triggers a cache update
        request.session.delete(period)

    return delete_period


@cli.command(name='compute-occasion-durations')
def compute_occasion_durations(
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """ Recomputes the durations of all occassions.

    Example::

        onegov-feriennet --select /foo/bar compute-occasion-durations

    """

    def compute_occasion_durations(
        request: FeriennetRequest,
        app: FeriennetApp
    ) -> None:

        occasions = request.session.query(Occasion)

        for o in occasions:
            o.duration = o.compute_duration(o.dates)

    return compute_occasion_durations


@cli.command('migrate-feriennet', context_settings={'default_selector': '*'})
@pass_group_context
def migrate_feriennet(
    group_context: GroupContext
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """ Migrates the database from an old feriennet to the new feriennet like
    in the upgrades.

    """

    def migrate_to_new_feriennet(request: FeriennetRequest,
                                 app: FeriennetApp) -> None:
        context: UpgradeContext = Bunch(session=app.session())  # type:ignore
        migrate_theme_options(context)
        migrate_homepage_structure_for_feriennet(context)

    return migrate_to_new_feriennet
