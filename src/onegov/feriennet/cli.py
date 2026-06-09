from __future__ import annotations

import click
import transaction

from onegov.activity import Activity
from onegov.activity.models import BookingPeriod
from onegov.activity.models import Occasion
from onegov.activity.models import Volunteer
from onegov.core.cli import command_group
from sqlalchemy import text


from typing import TYPE_CHECKING

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


@cli.command(name='delete-activity', context_settings={'singular': True})
@click.argument('name')
def delete_activity(
    name: str
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """ Deletes activities with name (not Title).

    Example::

        onegov-feriennet --select /foo/bar activity "mandala-malen"

    """

    def delete_activity(
        request: FeriennetRequest,
        app: FeriennetApp
    ) -> None:

        activity = request.session.query(
            Activity).filter_by(name=name).first()

        if not activity:
            raise click.ClickException(f'Could not find activity «{name}»')

        request.session.delete(activity)

    return delete_activity


@cli.command('strip-whitespace-from-names')
@click.option('--dry-run/--no-dry-run', default=False)
def strip_whitespace_from_names(
    dry_run: bool
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """ Strips leading/trailing whitespace from first_name and last_name
    of all volunteers.

    Example:

        `onegov-feriennet --select /onegov_feriennet/*
        strip-whitespace-from-names`

    """

    def _strip(
        request: FeriennetRequest,
        app: FeriennetApp
    ) -> None:
        session = app.session()
        count = 0
        for volunteer in session.query(Volunteer):
            first_name = volunteer.first_name.strip()
            last_name = volunteer.last_name.strip()
            if (first_name, last_name) != (
                volunteer.first_name,
                volunteer.last_name,
            ):
                volunteer.first_name = first_name
                volunteer.last_name = last_name
                count += 1

        if dry_run:
            transaction.abort()
            click.secho('Aborting transaction', fg='yellow')

        click.secho(
            f'{app.schema}: Stripped whitespace from {count} volunteer(s)',
            fg='green'
        )

    return _strip
