""" Provides commands related to the onegov.event.

Use this **for debugging/development only**.

Example::

    onegov-event clear govikon

"""

import bleach
import click
import requests
import transaction

from datetime import timedelta
from dateutil.parser import parse
from lxml import objectify
from onegov.core.orm import Base, SessionManager
from onegov.event import EventCollection
from onegov.server.config import Config


class Empty():
    text = None


class Context(object):

    def __init__(self, config, namespace):
        self.config = config
        self.namespace = namespace

    @property
    def appconfigs(self):
        for appcfg in self.config.applications:
            if self.namespace != '*' and self.namespace != appcfg.namespace:
                continue

            yield appcfg


@click.group()
@click.option('--config',
              default='onegov.yml',
              help="The config file to use (default is onegov.yml)")
@click.option('--namespace',
              default='*',
              help=(
                  "The namespace to run this command on (see onegov.yml). "
                  "If no namespace is given, all namespaces are updated. "
              ))
@click.pass_context
def cli(ctx, config, namespace):
    ctx.obj = Context(Config.from_yaml_file(config), namespace)


@cli.command()
@click.option('--confirm/--no-confirm', default=True,
              help="Ask for confirmation (disabling this is dangerous!)")
@click.argument('town')
@click.pass_context
def clear(ctx, confirm, town):
    """ Deletes all events for the given town. """

    if ctx.obj.namespace == '*':
        click.confirm(
            "Are you sure that you want to update all namespaces?",
            default=False, abort=True
        )

    if confirm:
        click.confirm(
            "Do you really want override all your local data?",
            default=False, abort=True
        )

    for appcfg in ctx.obj.appconfigs:

        dsn = appcfg.configuration.get('dsn')
        if dsn:
            schema = '{}-{}'.format(appcfg.namespace, town)
            print("Processing {}".format(schema))

            mgr = SessionManager(dsn, base=Base)
            mgr.set_current_schema(schema)

            events = EventCollection(mgr.session())

            print("  Deleting {} events.".format(events.query().count()))
            for event in events.query():
                events.delete(event)

            transaction.commit()


@cli.command(name='guidle-import')
@click.argument('town')
@click.argument('url')
@click.pass_context
def guidle_import(ctx, town, url):
    """ Imports events from guilde to the given town. """

    if ctx.obj.namespace == '*':
        click.confirm(
            "Are you sure that you want to update all namespaces?",
            default=False, abort=True
        )

    print("Downloading events at {0}".format(url))
    root = objectify.fromstring(bytes(requests.get(url).text, 'utf-8'))
    offers = root.xpath(
        '*//guidle:offer', namespaces={'guidle': 'http://www.guidle.com'}
    )

    for appcfg in ctx.obj.appconfigs:

        dsn = appcfg.configuration.get('dsn')
        if not dsn:
            continue

        schema = '{}-{}'.format(appcfg.namespace, town)
        print("Processing {}".format(schema))

        mgr = SessionManager(dsn, base=Base)
        mgr.set_current_schema(schema)
        event_collection = EventCollection(mgr.session())

        for index, offer in enumerate(offers):
            print("  Importing offer {}/{}".format(index + 1, len(offers)))

            for date in [d for d in offer.schedules.iterchildren()]:
                # parse start, end, recurrence
                start = parse(getattr(date, 'startDate', Empty).text)
                end = getattr(date, 'endDate', Empty).text
                try:
                    weekdays = list(date.weekdays.iterchildren())
                    recurrence = 'RRULE:FREQ=WEEKLY;BYDAY=%s' % ','.join(
                        [d.text.upper() for d in weekdays]
                    )
                except AttributeError:
                    recurrence = ''

                if end and not recurrence:
                    end = parse(end)
                    if start != end:
                        until = end + timedelta(days=1)
                        recurrence = 'RRULE:FREQ=DAILY;UNTIL={}'.format(
                            until.strftime('%Y%m%dT%H%MZ')
                        )
                        end = start
                else:
                    if recurrence:
                        until = parse(end) + timedelta(days=1)
                        recurrence += ';UNTIL={}'.format(
                            until.strftime('%Y%m%dT%H%MZ')
                        )
                    end = start

                # parse start and end times
                start_time = getattr(date, 'startTime', Empty).text
                end_time = getattr(date, 'endTime', Empty).text
                if start_time == end_time and recurrence:
                    start_time = None
                    end_time = None
                if start_time:
                    start = parse(start_time, default=start)
                if end_time:
                    end = parse(end_time, default=end)
                if end < start:
                    end += timedelta(days=1)

                # parse description and location
                description = []
                for att in ('longDescription', 'openingHours',
                            'priceInformation', 'externalLink', 'homepage',
                            'ticketingUrl'):
                    description.append(
                        bleach.clean(
                            getattr(offer.offerDetail, att, Empty).text,
                            tags=[]
                        )
                    )
                description.append('\n')
                for att in ('company', 'street', 'zip', 'city'):
                    description.append(
                        bleach.clean(
                            getattr(offer.address, att, Empty).text,
                            tags=[]
                        )
                    )
                description.append('\n')
                for att in ('company', 'name', 'email', 'telephone_1'):
                    description.append(
                        bleach.clean(
                            getattr(offer.contact, att, Empty).text,
                            tags=[]
                        )
                    )
                description = '\n'.join([d for d in description if d])
                location = bleach.clean(
                    getattr(offer.address, 'company', Empty).text,
                    tags=[]
                )

                # parse tags
                tags = []
                for classification in offer.classifications.iterchildren():
                    if classification.attrib.get('type') == 'PRIMARY':
                        tags.extend([
                            c.attrib.get('name', '')
                            for c in classification.iterchildren()
                        ])
                tags = [tag for tag in set(tags) if tag]

                # add event
                event = event_collection.add(
                    title=offer.offerDetail.title.text,
                    start=start,
                    end=end,
                    timezone='Europe/Zurich',
                    recurrence=recurrence,
                    location=location,
                    tags=tags,
                    content={'description': description}
                )
                event.submit()
                event.publish()

            transaction.commit()
