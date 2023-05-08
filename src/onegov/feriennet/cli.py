import click
import sys

from onegov.core.cli import command_group
from onegov.activity.models import Period
from sqlalchemy import text


cli = command_group()


@cli.command(name='delete-period', context_settings={'singular': True})
@click.argument('title')
def delete_period(title):
    """ Deletes all the data associated with a period, including:

    - Payments
    - Bookings
    - Occasions
    - Publication Requests
    - Tickets

    We usually don't allow for this, but there tends to be a request here and
    there about this, where a Ferienpass created a period for testing and
    tries to return to a semi-clean state.

    Example:

        onegov-feriennet --select /foo/bar delete-period "Ferienpass Test"

    """

    def delete_period(request, app):
        period = request.session.query(Period).filter_by(title=title).first()

        if not period:
            print(f"Could not find period «{title}»")
            sys.exit(1)

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
