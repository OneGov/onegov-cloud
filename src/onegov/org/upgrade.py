""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from __future__ import annotations

import click
import pytz
import re
import yaml

from itertools import chain
from onegov.core.crypto import random_token
from onegov.core.orm import Base, find_models
from onegov.core.orm.types import JSON, UTCDateTime, UUID
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.core.utils import normalize_for_url
from onegov.directory import DirectoryEntry
from onegov.directory.models.directory import DirectoryFile
from onegov.file import File
from onegov.form import FormDefinition
from onegov.newsletter import Newsletter
from onegov.org.models import (
    Organisation, Topic, News, ExtendedDirectory, PushNotification)
from onegov.org.models.political_business import (
    POLITICAL_BUSINESS_STATUS, POLITICAL_BUSINESS_TYPE)
from onegov.org.utils import annotate_html
from onegov.page import Page, PageCollection
from onegov.people import Person
from onegov.reservation import Resource
from onegov.ticket import TicketPermission
from onegov.user import User, UserGroup
from sqlalchemy import Column, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import undefer, selectinload, load_only


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


@upgrade_task('Move from town to organisation', always_run=True)
def move_town_to_organisation(context: UpgradeContext) -> bool | None:

    # if the organisations table does not exist (other modules), skip
    has_organisations = context.app.session_manager.session().execute("""
        select exists (select 1 from information_schema.tables
        where table_schema='{}' and table_name='organisations')
    """.format(context.app.schema)).scalar()

    has_towns = context.app.session_manager.session().execute("""
        select exists (select 1 from information_schema.tables
        where table_schema='{}' and table_name='towns')
    """.format(context.app.schema)).scalar()

    if not has_organisations or not has_towns:
        return False

    # this needs to be an always-run task for now, since on first install the
    # module is deteced as new and it is assumed that no tasks need to be run
    # as a result
    if context.session.query(Organisation).first():
        return False

    context.operations.drop_table('organisations')
    context.operations.rename_table('towns', 'organisations')
    return None


@upgrade_task('Add image-dimensions to html')
def add_image_dimensions_to_html(context: UpgradeContext) -> None:
    for topic in context.session.query(Topic):
        topic.text = annotate_html(topic.text, context.request)

    for news in context.session.query(News):
        news.text = annotate_html(news.text, context.request)

    for resource in context.session.query(Resource):
        if not hasattr(resource, 'text'):
            continue

        resource.text = annotate_html(resource.text, context.request)

    for form in context.session.query(FormDefinition):
        form.text = annotate_html(form.text, context.request)


@upgrade_task('Remove official notices table')
def remove_official_notices_table(context: UpgradeContext) -> bool | None:
    # an incompatible release was accidentally left in, so we remove the
    # table in such instances, triggering a recreation on the next start

    if not context.has_table('official_notices'):
        return False

    session = context.app.session_manager.session()

    organisations_count = session.execute('select count(*) from organisations')
    if organisations_count.scalar() != 1:
        return False

    notices_count = session.execute('select count(*) from official_notices')
    if notices_count.scalar() != 0:
        return False

    context.operations.drop_table('official_notices')
    return None


@upgrade_task('Add new defaults to existing directories')
def add_new_defaults_to_existing_directories(context: UpgradeContext) -> None:
    for directory in context.session.query(ExtendedDirectory):
        directory.enable_submissions = False
        directory.price = 'free'
        directory.currency = 'CHF'


@upgrade_task('Migrate enable_map option')
def migrate_enable_map_option(context: UpgradeContext) -> None:
    for directory in context.session.query(ExtendedDirectory):
        directory.enable_map = directory.enable_map and 'everywhere' or 'no'


@upgrade_task('Fix directory order')
def fix_directory_order(context: UpgradeContext) -> None:
    for directory in context.session.query(ExtendedDirectory):
        directory.order = normalize_for_url(directory.title)


@upgrade_task('Add default redirect setting')
def add_default_recirect_setting(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org:
        org.redirect_homepage_to = 'no'


@upgrade_task('Rename guideline to submissions_guideline')
def rename_guideline_to_submissions_guideline(context: UpgradeContext) -> None:
    directories = (
        context.session.query(ExtendedDirectory)
        .options(undefer(ExtendedDirectory.content))
    )

    for directory in directories:
        directory.content['submissions_guideline'] = (
            directory.content.pop('guideline', None))


@upgrade_task('Extend content people with show_function property in tuple')
def add_content_show_property_to_people(context: UpgradeContext) -> None:
    q = PageCollection(context.session).query()
    q = q.filter(Topic.type == 'topic')
    pages = q.filter(Topic.content['people'].isnot(None))

    def is_already_updated(people_item: Sequence[Any]) -> bool:
        return len(people_item) == 2 and isinstance(people_item[1], bool)

    for page in pages:
        updated_people = []
        for person in page.content['people']:
            if len(person) == 2 and not is_already_updated(person[1]):
                # (id, function) -> (id, (function, show_function))
                updated_people.append([person[0], (person[1], True)])
            else:
                updated_people.append(person)
        page.content['people'] = updated_people


@upgrade_task('Add meta access property')
def add_meta_access_property(context: UpgradeContext) -> None:
    def has_meta_property(model: type[Base]) -> bool:
        if not hasattr(model, 'meta'):
            return False

        assert isinstance(model.meta.property.columns[0].type, JSON)
        return True

    for model in find_models(Base, has_meta_property):
        table = model.__tablename__

        # We use update statements here because we need to touch a lot of data.
        #
        # THIS IS UNSAFE, DO NOT COPY & PASTE
        context.session.execute(f"""
            UPDATE {table} SET meta = meta || jsonb '{{"access": "private"}}'
            WHERE (meta->>'is_hidden_from_public')::boolean = TRUE;

            UPDATE {table} SET meta = meta - 'is_hidden_from_public'
            WHERE meta ? 'is_hidden_from_public';
        """)


@upgrade_task('Rerender organisation html')
def add_rerender_organsiation_html(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if not org:
        return

    if org.contact is not None:
        org.contact = org.contact

    if org.opening_hours is not None:
        org.opening_hours = org.opening_hours


@upgrade_task("Migrate FormFile's attached to DirectoryEntry to DirectoryFile")
def fix_directory_file_identity(context: UpgradeContext) -> None:
    # Not sure of this doubles the files, but actually the file
    # reference remains, so it shouldn't
    for entry in context.session.query(DirectoryEntry).all():
        for field in entry.directory.file_fields:
            field_data = entry.content['values'][field.id]
            if field_data and field_data.get('data', '').startswith('@'):
                file_id = field_data['data'].lstrip('@')
                file = context.session.query(File).filter_by(
                    id=file_id).first()
                if file and file.type != 'directory':
                    new = DirectoryFile(  # type:ignore[misc]
                        id=random_token(),
                        name=file.name,
                        note=file.note,
                        reference=file.reference
                    )
                    entry.files.append(new)
                    entry.content['values'][field.id]['data'] = f'@{new.id}'
                    entry.content.changed()  # type:ignore[attr-defined]


@upgrade_task('Cache news hashtags in meta')
def cache_news_hashtags_in_meta(context: UpgradeContext) -> None:
    try:
        for news in context.session.query(News):
            news.hashtags = news.fts_tags or []
    except Exception:  # nosec B110
        pass


@upgrade_task('Change daily_ticket_statistics data format')
def change_daily_ticket_statistics_data_format(
    context: UpgradeContext
) -> None:

    users = context.session.query(User).options(undefer(User.data))
    unset = object()

    for user in users:
        if not user.data:
            continue

        daily = user.data.pop('daily_ticket_statistics', unset)
        if daily is unset:
            continue

        user.data.setdefault(
            'ticket_statistics',
            'daily' if daily else 'never'
        )


@upgrade_task('Fix content people for models that use PersonLinkExtension')
def fix_content_people_for_models_that_use_person_link_extension(
    context: UpgradeContext
) -> None:

    iterables: list[Iterable[Page | FormDefinition | Resource]] = []
    if context.has_table('pages'):
        pages = context.session.query(Page)
        pages = pages.filter(Page.content['people'].isnot(None))
        iterables.append(pages)
    if context.has_table('forms'):
        forms = context.session.query(FormDefinition)
        forms = forms.filter(FormDefinition.content['people'].isnot(None))
        iterables.append(forms)
    if context.has_table('resources'):
        resources = context.session.query(Resource)
        resources = resources.filter(Resource.content['people'].isnot(None))
        iterables.append(resources)

    def is_already_updated(people_item: Sequence[Any]) -> bool:
        return len(people_item) == 2 and isinstance(people_item[1], bool)

    for obj in chain(*iterables):
        updated_people = []
        for person in obj.content['people']:
            if len(person) == 2 and not is_already_updated(person[1]):
                # (id, function) -> (id, (function, show_function))
                updated_people.append([person[0], (person[1], True)])
            else:
                updated_people.append(person)
        obj.content['people'] = updated_people


@upgrade_task('Fix nested list in content people')
def fix_nested_list_in_content_people(context: UpgradeContext) -> None:
    iterables: list[Iterable[Page | FormDefinition | Resource]] = []
    if context.has_table('pages'):
        pages = context.session.query(Page)
        pages = pages.filter(Page.content['people'].isnot(None))
        iterables.append(pages)
    if context.has_table('forms'):
        forms = context.session.query(FormDefinition)
        forms = forms.filter(FormDefinition.content['people'].isnot(None))
        iterables.append(forms)
    if context.has_table('resources'):
        resources = context.session.query(Resource)
        resources = resources.filter(Resource.content['people'].isnot(None))
        iterables.append(resources)

    def is_broken(people_item: Sequence[Any]) -> bool:
        return (
            len(people_item) == 2
            and isinstance(people_item[0], list)
        )

    for obj in chain(*iterables):
        updated_people = []
        for person in obj.content['people']:
            if len(person) == 2 and is_broken(person[1]):
                # (id, ((function, show), show)) -> (id, (function, show))
                updated_people.append([person[0], (person[1][0][0], True)])
            else:
                updated_people.append(person)
        obj.content['people'] = updated_people


@upgrade_task('Add explicit link for files linked in content')
def add_files_linked_in_content(context: UpgradeContext) -> None:
    iterables: list[
        Iterable[Page | FormDefinition | Resource | ExtendedDirectory]
    ] = []
    if context.has_table('pages'):
        pages = context.session.query(Page)
        iterables.append(pages)
    if context.has_table('forms'):
        forms = context.session.query(FormDefinition)
        iterables.append(forms)
    if context.has_table('resources'):
        resources = context.session.query(Resource)
        iterables.append(resources)
    if context.has_table('directories'):
        directories = context.session.query(ExtendedDirectory)
        iterables.append(directories)

    for obj in chain(*iterables):
        if not hasattr(obj, 'content_file_link_observer'):
            continue

        # this should automatically link any unlinked files
        obj.content_file_link_observer({'text'})


@upgrade_task('Add submission window id to survey submissions')
def add_submission_window_id_to_survey_submissions(
    context: UpgradeContext
) -> None:
    if not context.has_column('survey_submissions', 'submission_window_id'):
        context.add_column_with_defaults(
            'survey_submissions',
            Column(
                'submission_window_id',
                UUID,
                ForeignKey('submission_windows.id'),
                nullable=True
            ),
            default=None
        )


@upgrade_task('Remove stored contact_html and opening_hours_html')
def remove_stored_contact_html_and_opening_hours_html(
    context: UpgradeContext
) -> None:

    # Organisation
    if context.has_table('organisations'):
        org = context.session.query(Organisation).first()
        if org:
            if 'contact_html' in org.meta:
                del org.meta['contact_html']

            if 'opening_hours_html' in org.meta:
                del org.meta['opening_hours_html']

    # ContactExtension
    iterables: list[Iterable[Page | FormDefinition | Resource]] = []
    if context.has_table('pages'):
        pages = context.session.query(Page)
        iterables.append(pages)
    if context.has_table('forms'):
        forms = context.session.query(FormDefinition)
        iterables.append(forms)
    if context.has_table('resources'):
        resources = context.session.query(Resource)
        iterables.append(resources)

    for obj in chain(*iterables):
        if not getattr(obj, 'content', None):
            continue

        if 'contact_html' in obj.content:
            del obj.content['contact_html']


@upgrade_task('Add CASCADE delete to push notification foreign key')
def add_cascade_delete_to_push_notification(context: UpgradeContext) -> None:
    if not context.has_table('push_notification'):
        return

    constraint_name = 'push_notification_news_id_fkey'
    schema_name = context.app.schema

    if context.has_constraint('push_notification',
            'push_notification_news_id_fkey',
            'FOREIGN KEY'
    ):
        print(f'Dropping and recreating {constraint_name} in {schema_name}')

        context.operations.drop_constraint(
            constraint_name,
            'push_notification',
            type_='foreignkey'
        )
        context.operations.create_foreign_key(
            constraint_name,
            'push_notification', 'pages',
            ['news_id'], ['id'],
            ondelete='CASCADE'
        )


@upgrade_task('Convert push_notification.sent_at to UTCDateTime correctly')
def convert_sent_at_to_utc_datetime(context: UpgradeContext) -> None:
    if not context.has_column('push_notification', 'sent_at'):
        return

    notifications = context.session.query(PushNotification).all()
    zurich = pytz.timezone('Europe/Zurich')

    for notification in notifications:
        if notification.sent_at:
            # Check if the datetime is naive (no tzinfo)
            if notification.sent_at.tzinfo is None:
                # Localize naive datetime
                localized = zurich.localize(notification.sent_at)
            else:
                # If it's already timezone-aware, just convert it to UTC
                localized = notification.sent_at.astimezone(pytz.UTC)

            notification.sent_at = localized

    context.session.flush()
    context.operations.alter_column(
        'push_notification', 'sent_at', type_=UTCDateTime
    )


@upgrade_task('Create hierarchy and move organisations to content')
def create_hierarchy_and_move_organisations_to_content(
    context: UpgradeContext
) -> None:
    session = context.app.session()
    # Use only columns that definitely exist to avoid error
    people = session.query(Person).options(
        load_only('id', 'content')
    ).all()
    hierarchy: dict[str, set[str]] = {}
    for person in people:
        org = person.content.get('organisation')
        if org:
            # Create hierarchy from existing organisation and
            # sub_organisation of people
            hierarchy.setdefault(org, set())
            sub_org = person.content.get('sub_organisation')
            if sub_org:
                hierarchy[org].add(sub_org)
            # Move organisation and sub_organisation to content
            person.content['organisations_multiple'] = [
                org, f'-{sub_org}'
            ] if sub_org else [org]

    hierarchy_yaml = ''
    for org, sub_orgs in hierarchy.items():
        hierarchy_yaml += f'- {org}:\n'
        for sub_org in sub_orgs:
            hierarchy_yaml += f'  - {sub_org}\n'
    if hierarchy_yaml:
        data = yaml.safe_load(hierarchy_yaml)
        organisation = session.query(Organisation).first()
        if organisation:
            organisation.organisation_hierarchy = data
    session.flush()


@upgrade_task('Convert directories setting on UserGroup to ticket permissions')
def convert_directories_to_ticket_permissions(context: UpgradeContext) -> None:
    if not hasattr(UserGroup, 'ticket_permissions'):
        return

    permission: TicketPermission
    for user_group in context.session.query(UserGroup).filter(
        UserGroup.meta['directories'].isnot(None)
    ).options(selectinload(UserGroup.ticket_permissions)):
        directories = set(user_group.meta['directories'])
        assert hasattr(user_group, 'ticket_permissions')
        for permission in user_group.ticket_permissions:
            if permission.handler_code != 'DIR':
                continue

            if permission.group is None:
                continue

            if permission.group in directories:
                directories.discard(permission.group)
                permission.immediate_notification = True

        for group in directories:
            permission = TicketPermission(
                handler_code='DIR',
                group=group,
                user_group=user_group,
                exclusive=False,
                immediate_notification=True,
            )
            context.session.add(permission)

        del user_group.meta['directories']


@upgrade_task('Set default extras pricing method on existing resources')
def set_default_extras_pricing_method(context: UpgradeContext) -> None:
    if not context.has_table('resources'):
        return

    # In order to keep the behavior of existing resources with priced
    # extras the same we need to set them to "one_off", the new default
    # will be "per_item"
    for resource in (
        context.session.query(Resource)
        .filter(Resource.definition.isnot(None))
    ):
        resource.extras_pricing_method = 'one_off'


@upgrade_task('Add party column to par_parliamentarians')
def add_party_column_to_par_parliamentarians(context: UpgradeContext) -> None:
    if not context.has_column('par_parliamentarians', 'party'):
        context.add_column_with_defaults(
            'par_parliamentarians',
            Column(
                'party',
                Text,
                nullable=True
            ),
            default=None
        )


@upgrade_task('Migrate Kaba config to new format')
def migrate_kaba_config_to_new_format(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()
    if org is None:
        return

    site_id = org.meta.pop('kaba_site_id', None)
    api_key = org.meta.pop('kaba_api_key', None)
    api_secret = org.meta.pop('kaba_api_secret', None)
    if not (site_id and api_key and api_secret):
        return

    org.meta['kaba_configurations'] = [{
        'site_id': site_id,
        'api_key': api_key,
        'api_secret': api_secret,
    }]

    if context.has_table('resources'):
        # update kaba_components to new format
        context.session.execute("""
            UPDATE resources
               SET meta = jsonb_set(
                   meta,
                   '{kaba_components}',
                   to_jsonb(ARRAY(
                       SELECT jsonb_build_array(:site_id, value)
                         FROM jsonb_array_elements(meta->'kaba_components')
                   ))
                )
             WHERE meta ? 'kaba_components'
        """, {'site_id': site_id})

    if context.has_table('reservations'):
        # update visits to new format
        context.session.execute("""
            UPDATE reservations
               SET data = jsonb_set(
                   data,
                   '{kaba,visit_ids}',
                   jsonb_build_object(:site_id, data->'kaba'->'visit_id')
                ) #- '{kaba,visit_id}'
             WHERE data ? 'kaba'
               AND data->'kaba' ? 'visit_id'
        """, {'site_id': site_id})


@upgrade_task('Update political business enum values')
def update_political_business_enum_values(
    context: UpgradeContext
) -> None:
    if context.has_enum('par_political_business_type'):
        context.update_enum_values(
            'par_political_business_type',
            POLITICAL_BUSINESS_TYPE.keys()
        )
    if context.has_enum('par_political_business_status'):
        context.update_enum_values(
            'par_political_business_status',
            POLITICAL_BUSINESS_STATUS.keys()
        )


@upgrade_task('Change political business participation type column type')
def change_political_business_participation_type_column_type(
    context: UpgradeContext
) -> None:
    table = 'par_political_business_participants'
    if context.has_table(table) and context.has_column(
        table,
        'participant_type'
    ):
        context.operations.alter_column(
            'par_political_business_participants',
            'participant_type',
            type_=Text,
        )


@upgrade_task('Remove obsolete polymorphic type columns')
def remove_obsolete_polymorphic_type_columns(context: UpgradeContext) -> None:
    for table in (
        'par_attendence',
        'par_parties',
        'par_changes',
        'par_legislative_periods',
        'par_political_businesses',
        'par_political_business_participants',
    ):
        column = 'poly_type' if table == 'par_attendence' else 'type'
        if context.has_table(table) and context.has_column(table, column):
            context.operations.drop_column(table, column)


@upgrade_task('Make political business participation type column nullable')
def make_political_business_participation_type_column_nullable(
    context: UpgradeContext
) -> None:
    table = 'par_political_business_participants'
    if context.has_table(table) and context.has_column(
        table,
        'participant_type'
    ):
        context.operations.alter_column(
            table,
            'participant_type',
            nullable=True,
        )


@upgrade_task('Update political business type enum values')
def update_political_business_type_enum_values(
    context: UpgradeContext
) -> None:

    new_business_type = Enum(
        *POLITICAL_BUSINESS_TYPE.keys(),
        name='par_political_business_type',
    )

    if context.has_enum('par_political_business_type'):
        op = context.operations

        op.execute("""
            ALTER TABLE par_political_businesses
            ALTER COLUMN political_business_type TYPE Text;
            UPDATE par_political_businesses
            SET political_business_type = 'interpellation'
            WHERE political_business_type = 'interpelleation';
            UPDATE par_political_businesses
            SET political_business_type = 'election'
            WHERE political_business_type = 'elections';
            UPDATE par_political_businesses
            SET political_business_type = 'miscellaneous'
            WHERE political_business_type = 'proposal';
            UPDATE par_political_businesses
            SET political_business_type = 'miscellaneous'
            WHERE political_business_type = 'mandate';
            UPDATE par_political_businesses
            SET political_business_type = 'miscellaneous'
            WHERE political_business_type = 'communication';
            UPDATE par_political_businesses
            SET political_business_type = 'miscellaneous'
            WHERE political_business_type = 'report';
            DROP TYPE par_political_business_type;
        """)

        new_business_type.create(op.get_bind())

        op.execute("""
            ALTER TABLE par_political_businesses
            ALTER COLUMN political_business_type
            TYPE par_political_business_type
            USING political_business_type::text::par_political_business_type;
        """)


@upgrade_task('Cache new news hashtags in meta')
def cache_new_news_hashtags_in_meta(context: UpgradeContext) -> None:
    try:
        for news in context.session.query(News):
            news.hashtags = news.fts_tags or []
    except Exception:  # nosec B110
        pass


@upgrade_task('Add show_only_previews column to newsletters')
def add_show_only_previews_column_to_newsletters(
    context: UpgradeContext) -> None:
    if not context.has_table('newsletters'):
        return

    if context.has_column('newsletters', 'show_only_previews'):
        return

    context.add_column_with_defaults(
        'newsletters',
        Column(
            'show_only_previews',
            Boolean,
            nullable=False,
            default=False
        ),
        default=False
    )

    newsletters = context.session.query(Newsletter).all()
    for newsletter in newsletters:
        newsletter.show_only_previews = newsletter.content.get(
            'show_news_as_tiles', False)
        newsletter.content.pop('show_news_as_tiles', None)

    context.session.flush()


@upgrade_task('Migrate away from free-text analytics code')
def migrate_analytics_code(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org is None or 'analytics_code' not in org.meta:
        return

    analytics_seantis_re = re.compile(
        r'data-domain="([^"]+)" src="https://analytics\.seantis\.ch'
    )
    matomo_re = re.compile(
        r"""var u="([^"]+)";.*?'setSiteId', '([0-9]+)'"""
    )
    siteimprove_re = re.compile(
        r'https://siteimproveanalytics\.com/js/siteanalyze_([0-9]+)\.js'
    )
    google_analytics_re = re.compile(
        r'"https://www\.googletagmanager\.com/gtag/js\?id=([^"]+)"'
    )

    code = org.meta.pop('analytics_code')
    if match := analytics_seantis_re.search(code):
        org.analytics_provider_name = 'analytics.seantis.ch'
        org.plausible_domain = match.group(1)
    elif match := matomo_re.search(code):
        matomo_url = match.group(1)
        if 'stats.seantis.ch' in matomo_url:
            org.analytics_provider_name = 'stats.seantis.ch'
        elif 'matomo.zug.ch' in matomo_url:
            org.analytics_provider_name = 'matomo.zug.ch'
        elif 'webcloud7.opsone-analytics.ch' in matomo_url:
            org.analytics_provider_name = 'webcloud7.opsone-analytics.ch'
        else:
            click.secho(
                f'Dropped unknown matomo analytics instance {matomo_url}',
                fg='red'
            )
            return
        org.matomo_site_id = int(match.group(2))
    elif match := google_analytics_re.search(code):
        org.analytics_provider_name = 'google_analytics'
        org.google_tag_id = match.group(1)
    elif match := siteimprove_re.search(code):
        org.analytics_provider_name = 'siteimprove'
        org.siteimprove_site_id = int(match.group(1))
    else:
        click.secho('Dropped unrecognized analytics code:')
        click.echo(code)
