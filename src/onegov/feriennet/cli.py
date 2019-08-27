import click
import random

from datetime import timedelta
from faker import Faker
from functools import partial
from onegov.activity import OccasionCollection
from onegov.activity.models.activity import ACTIVITY_STATES
from onegov.core.cli import command_group
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.forms.activity import TAGS
from onegov.user import UserCollection


cli = command_group()


@cli.command(name='generate-activities', context_settings={'singular': True})
@click.option('--count', default=1000)
def generate_activities(count):
    """ Randomly generates activities/occasions and bookings for
    performance tests.

    """

    fake = Faker()
    tags = [t[0] for t in TAGS]

    def maybe():
        return random.choice((True, False))

    def maybe_repeat(fn):
        result = fn()

        def wrapper():
            nonlocal result

            if maybe():
                result = fn()

            return result

        return wrapper

    def random_age():
        min_age = random.randint(0, 15)
        max_age = random.randint(min_age, 20)

        return min_age, max_age

    def random_spots():
        min_spots = random.randint(0, 10)
        max_spots = random.randint(min_spots, 30)

        return min_spots, max_spots

    def random_dates():
        start = fake.date_time_this_year(before_now=True)
        start = start.replace(
            second=0,
            microsecond=0,
            minute=start.minute - (start.minute % 15)
        )

        end = start + timedelta(hours=random.randint(0, 96))

        return start, end

    def generate_activity(request, app, owner, activities, occasions):
        activity = activities.add(
            title=fake.text(50).rstrip('.'),
            lead=fake.text(150),
            text=fake.text(500),
            username=owner,
            tags=random.sample(tags, k=random.randint(0, 8))
        )
        activity.state = random.choice(ACTIVITY_STATES)

        dates = maybe_repeat(random_dates)
        age = maybe_repeat(random_age)
        spots = maybe_repeat(random_spots)

        for i in range(0, random.randint(0, 8)):

            start, end = dates()

            occasions.add(
                activity=activity,
                start=start,
                end=end,
                age=age(),
                spots=spots(),
                timezone='Europe/Zurich',
                location=maybe() and fake.city() or None,
                note=maybe() and fake.text(random.randint(5, 100)) or None,
            )

    def generate(request, app):
        owners = [
            u.username for u in
            UserCollection(app.session()).by_roles('admin', 'editor')
        ]

        session = app.session()

        bound_generate_activity = partial(
            generate_activity,
            request=request,
            app=app,
            activities=VacationActivityCollection(session, identity=None),
            occasions=OccasionCollection(session),
        )

        for n in range(0, count):
            bound_generate_activity(owner=random.choice(owners))

    return generate
