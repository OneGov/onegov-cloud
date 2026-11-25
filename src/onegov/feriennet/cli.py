import click
import transaction

from onegov.activity import Activity
from onegov.activity.models import Booking
from datetime import date, datetime, timedelta

from onegov.activity import (BookingPeriodCollection,
                             OccasionCollection)
from onegov.core.cli import command_group
from onegov.activity.models import BookingPeriod
from onegov.activity.models import Occasion
from onegov.activity.models import Volunteer
from sqlalchemy import text
from sqlalchemy.orm import joinedload


from typing import TYPE_CHECKING

from onegov.feriennet.collections.activity import VacationActivityCollection
from onegov.user import UserCollection

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


# a child can star at most this many wishes per period (see Booking.star and
# the feriennet toggle-star view)
STAR_CAP = 3


@cli.command(name='match-fairness', context_settings={'singular': False})
@click.argument('title', required=False)
def match_fairness(
    title: str | None
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """ Reports fairness statistics for a matched period (PRO-1428).

    Read-only. Run *after* a matching run to see how many favourites (starred
    wishes) went unfulfilled and whether children with many wishes are hit
    harder than children with few wishes - the effect of the absolute star
    cap of three favourites per child.

    Without a title the latest period (by execution start) is used, so the
    report can be run across all instances at once::

        onegov-feriennet --select '/*' match-fairness

        onegov-feriennet --select /foo/bar match-fairness "Ferienpass 2026"

    """

    def match_fairness(
        request: FeriennetRequest,
        app: FeriennetApp
    ) -> None:
        session = request.session

        if title is None:
            # only confirmed periods have been matched; a not-yet-matched
            # period would show every wish as unfulfilled
            period = (
                session.query(BookingPeriod)
                .filter(BookingPeriod.confirmed == True)
                .order_by(BookingPeriod.execution_start.desc())
                .first()
            )
            if not period:
                click.secho(f'{app.schema}: no matched period', fg='yellow')
                return
        else:
            period = session.query(
                BookingPeriod).filter_by(title=title).first()
            if not period:
                available = [
                    t for (t,) in session.query(BookingPeriod.title)
                    .order_by(BookingPeriod.execution_start.desc())
                    .limit(3)
                ]
                hint = (
                    '\nAvailable periods:\n  '
                    + '\n  '.join(f'«{t}»' for t in available)
                    if available else '\nNo periods exist in this instance.'
                )
                raise click.ClickException(
                    f'Could not find period «{title}».{hint}')

        # bookings are wishes; join Occasion since period is only reachable
        # through it. Exclude cancelled wishes and cancelled occasions (a
        # cancelled course is neither a real place nor a real blocker). Full
        # objects are loaded to reuse Booking.overlaps (minutes_between)
        query = (
            session.query(Booking)
            .join(Occasion, Booking.occasion_id == Occasion.id)
            .filter(Occasion.period_id == period.id)
            .filter(Occasion.cancelled.isnot(True))
            .filter(Booking.state != 'cancelled')
            .options(
                joinedload(Booking.occasion).joinedload(Occasion.dates),
                joinedload(Booking.period),
            )
        )

        # aggregate per attendee (child); keep the accepted and blocked-starred
        # booking objects to later tell real time conflicts from stale blocks
        per_child: dict[object, dict[str, int]] = {}
        child_bookings: dict[object, dict[str, list[Booking]]] = {}
        for b in query:
            accepted = b.state == 'accepted'
            child = per_child.setdefault(
                b.attendee_id,
                {'wishes': 0, 'starred': 0, 'starred_rejected': 0,
                 'starred_blocked': 0, 'starred_blocked_real': 0,
                 'starred_blocked_stale': 0, 'accepted': 0,
                 'nobbled': 0, 'nobbled_accepted': 0})
            objs = child_bookings.setdefault(
                b.attendee_id, {'accepted': [], 'blocked_starred': []})
            child['wishes'] += 1
            is_starred = b.starred
            child['starred'] += is_starred
            child['accepted'] += accepted
            if accepted:
                objs['accepted'].append(b)
            if is_starred:
                # 'open'/'denied' = no spot in an overbooked occasion (open
                # becomes denied once the period is confirmed); 'blocked' =
                # overlaps with an accepted booking of the same child
                if b.state in ('open', 'denied'):
                    child['starred_rejected'] += 1
                elif b.state == 'blocked':
                    child['starred_blocked'] += 1
                    objs['blocked_starred'].append(b)
            # nobbled: an admin prioritized this wish before the matching run,
            # so it wins its spot regardless of the child's own starring
            if b.nobbled:
                child['nobbled'] += 1
                child['nobbled_accepted'] += accepted

        # a blocked-starred wish is only a *real* conflict if it still overlaps
        # a currently accepted booking of the child; otherwise the blocker was
        # canceled after matching and the 'blocked' state is stale
        for attendee_id, objs in child_bookings.items():
            child = per_child[attendee_id]
            for bs in objs['blocked_starred']:
                if any(bs.overlaps(acc) for acc in objs['accepted']):
                    child['starred_blocked_real'] += 1
                else:
                    child['starred_blocked_stale'] += 1

        if not per_child:
            click.secho(
                f'{app.schema}: no bookings in «{period.title}»', fg='yellow')
            return

        def bucket(
            children: list[dict[str, int]]
        ) -> tuple[int, int, int, int, int, int]:
            starred = sum(c['starred'] for c in children)
            rejected = sum(c['starred_rejected'] for c in children)
            real = sum(c['starred_blocked_real'] for c in children)
            stale = sum(c['starred_blocked_stale'] for c in children)
            unplaced = sum(1 for c in children if c['accepted'] == 0)
            return len(children), starred, rejected, real, stale, unplaced

        few = [c for c in per_child.values() if c['wishes'] <= STAR_CAP]
        many = [c for c in per_child.values() if c['wishes'] > STAR_CAP]

        def pct(part: int, whole: int) -> str:
            return f'{part / whole * 100:.1f}%' if whole else 'n/a'

        click.secho(f'\n{app.schema}: fairness report for «{period.title}»',
                    fg='green', bold=True)
        click.echo(f'  children: {len(per_child)}, '
                   f'bookings: {sum(c["wishes"] for c in per_child.values())}')

        n, starred, rejected, real, stale, unplaced = bucket(
            list(per_child.values()))
        unfulfilled = rejected + real
        click.echo('\n  overall:')
        click.echo(f'    starred wishes unfulfilled (excl. stale): '
                   f'{unfulfilled}/{starred} ({pct(unfulfilled, starred)})')
        click.echo(f'      - rejected (no spot):        {rejected} '
                   f'({pct(rejected, starred)})')
        click.echo(f'      - overlapping (real conflict): {real} '
                   f'({pct(real, starred)})')
        click.echo(f'    stale blocked (blocker cancelled, ignored): {stale}')
        click.echo(f'    children with no place at all: {unplaced}/{n} '
                   f'({pct(unplaced, n)})')
        nobbled = sum(c['nobbled'] for c in per_child.values())
        nobbled_accepted = sum(
            c['nobbled_accepted'] for c in per_child.values())
        accepted_total = sum(c['accepted'] for c in per_child.values())
        click.echo(f'    admin-prioritized (nobbled, set before matching): '
                   f'{nobbled} wishes, of which accepted {nobbled_accepted} '
                   f'({pct(nobbled_accepted, accepted_total)} of all places)')

        click.echo('\n  by wishlist size (star cap = '
                   f'{STAR_CAP}):')
        for label, group in (
            (f'few wishes (<= {STAR_CAP})', few),
            (f'many wishes (> {STAR_CAP})', many),
        ):
            gn, gstarred, grej, greal, gstale, gunplaced = bucket(group)
            click.echo(f'    {label}: {gn} children, '
                       f'starred unfulfilled {grej + greal}/{gstarred} '
                       f'(rejected {grej}, overlapping {greal}; '
                       f'stale {gstale}), '
                       f'no place {gunplaced}/{gn} ({pct(gunplaced, gn)})')

    return match_fairness


VALID_PHASES = ('inactive', 'wishlist', 'booking', 'execution', 'payment')


@cli.command(name='which-ferienpass-is-currently',
             context_settings={'default_selector': '*'})
@click.argument('phase', required=True, type=click.Choice(VALID_PHASES))
def which_ferienpass(
    phase: str,
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """ Displays all ferienpass instances where the option applies.

    Example::
    onegov-feriennet --select /foo/bar which-ferienpass-is-currently 'phase'

    phases: inactive, wishlist, booking, execution, payment

    """
    def search_ferienpass(
        request: FeriennetRequest,
        app: FeriennetApp
    ) -> None:

        if not hasattr(app, 'active_period'):
            return

        if phase == 'inactive':
            if (
                not app.active_period or (
                    app.active_period.phase == 'inactive'
                )
            ):
                click.echo(f'{app.schema} - {app.org.title}')
        if not app.active_period:
            return
        else:
            period = app.active_period
            if phase == 'wishlist' and period.is_currently_prebooking:
                click.echo(f'{app.schema} - {app.org.title}')
                click.secho(
                    f'{period.prebooking_start} - {period.prebooking_end}',
                    fg='cyan'
                )
            if phase == 'booking' and period.is_currently_booking:
                click.echo(f'{app.schema} - {app.org.title}')
                click.secho(
                    f'{period.booking_start} - {period.booking_end}',
                    fg='cyan'
                )
            if phase == 'execution' and period.execution_phase:
                click.echo(f'{app.schema} - {app.org.title}')
                click.secho(
                    f'{period.execution_start} - {period.execution_end}',
                    fg='cyan'
                )
            if phase == 'payment' and period.payment_phase:
                click.echo(f'{app.schema} - {app.org.title}')

    return search_ferienpass


@cli.command(name='create-period-with-test-data')
@click.argument('phase')
@click.option('--confirmed', default=False, is_flag=True)
@click.option('--finalized', default=False, is_flag=True)
# @pass_group_context
def create_period_with_test_data(
    phase: str,
    finalized: bool,
    confirmed: bool
) -> Callable[[FeriennetRequest, FeriennetApp], None]:
    """Creates a period with 3 activities, 2 users and 2 attendees each.

    Usage:
    onegov-feriennet --select /onegov_feriennet/* create-period-with-test-data

    """
    def create_period(
        request: FeriennetRequest,
        app: FeriennetApp
    ) -> None:

        session = request.session
        now = datetime.now()

        def date_offset(offset: int) -> date:
            return (now + timedelta(days=offset)).date()

        # Create period
        periods = BookingPeriodCollection(session)
        nonlocal confirmed, finalized

        if phase == 'wishlist':
            prebooking = (date_offset(-1), date_offset(+1))
            booking = (date_offset(+1), date_offset(+10))
            execution = (date_offset(+10), date_offset(+20))

            period_values = {
                'title': f'Wunschtest {now.year}',
                'prebooking': prebooking,
                'booking': booking,
                'execution': execution,
            }

        elif phase == 'booking':
            prebooking = (date_offset(-10), date_offset(-5))
            booking = (date_offset(-5), date_offset(+5))
            execution = (date_offset(+5), date_offset(+10))
            confirmed = True

            period_values = {
                'title': f'Buchungstest {now.year}',
                'prebooking': prebooking,
                'booking': booking,
                'execution': execution,
            }

        elif phase == 'past':
            prebooking = (date_offset(-20), date_offset(-15))
            booking = (date_offset(-15), date_offset(-10))
            execution = (date_offset(-10), date_offset(-1))
            confirmed = True

            period_values = {
                'title': f'Vergangenheitstest {now.year}',
                'prebooking': prebooking,
                'booking': booking,
                'execution': execution,
            }
        else:
            raise NotImplementedError

        # register the orm cache keys in this process, so they get
        # evicted when we modify the periods table below
        for name in ('periods', 'active_period', 'periods_by_id'):
            getattr(app, name)

        period = periods.add(
            title=period_values['title'],  # type:ignore
            prebooking=period_values['prebooking'],  # type:ignore
            booking=period_values['booking'],  # type:ignore
            execution=period_values['execution'],  # type:ignore
            minutes_between=0,
            confirmable=True,
            finalizable=True,
            active=False,
        )

        period.activate()

        if confirmed:
            period.confirm_and_start_booking_phase()

        if finalized:
            period.finalized = True

        session.flush()

        click.secho(
            f'Created period {period_values["title"]}',
            fg='green'
        )

        # Create users
        users = UserCollection(session)
        emily = users.by_username('emily.larlham@mantics.org')
        if not emily:
            emily = users.add(
                'emily.larlham@mantics.org',
                'test',
                'member',
                realname='Emily Larlham'
            )
            click.secho('Created user: emily.larlham@mantics.org', fg='green')
        else:
            click.secho('User already exists: emily.larlham@mantics.org',
                        fg='cyan')

        zak = users.by_username('zak.george@revolution.com')
        if not zak:
            users.add(
                'zak.george@revolution.com',
                'test',
                'member',
                realname='Zak George'
            )
            click.secho('Created user: zak.george@revolution.com', fg='green')
        else:
            click.secho('User already exists: zak.george@revolution.com',
                        fg='cyan')

        # Create activities
        activities = VacationActivityCollection(session)
        dog_training = activities.add(
            title='Hundetraining',
            username='admin@example.org')
        click.secho('Created activity: Hundetraining', fg='green')
        dog_training.state = 'accepted'

        dance = activities.add(
            title='Tanzen',
            username='admin@example.org')
        click.secho('Created activity: Tanzen', fg='green')
        dance.state = 'accepted'

        # Create occasions
        occasions = OccasionCollection(session)

        occasions.add(
            activity=dog_training,
            start=datetime.combine(execution[0], now.time()),
            end=datetime.combine(
                execution[0], (now + timedelta(hours=3)).time()),
            timezone='Europe/Zurich',
            period=period
        )
        click.secho('Created occasion: Hundetraining', fg='green')

        occasions.add(
            activity=dance,
            start=datetime.combine(execution[0], now.time()),
            end=datetime.combine(
                execution[0], (now + timedelta(hours=3)).time()),
            timezone='Europe/Zurich',
            period=period
        )
        click.secho('Created occasion: Tanzen', fg='green')

    return create_period
