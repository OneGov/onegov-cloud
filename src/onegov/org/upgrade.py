""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from itertools import chain
from onegov.core.crypto import random_token
from onegov.core.orm import Base, find_models
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.core.utils import normalize_for_url
from onegov.directory import DirectoryEntry
from onegov.directory.models.directory import DirectoryFile
from onegov.file import File
from onegov.form import FormDefinition
from onegov.org.models import Organisation, Topic, News, ExtendedDirectory
from onegov.org.utils import annotate_html
from onegov.page import Page, PageCollection
from onegov.reservation import Resource
from onegov.user import User
from sqlalchemy import Column, ForeignKey
from onegov.core.orm.types import UUID
from sqlalchemy.orm import undefer


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

    if not context.has_table("official_notices"):
        return False

    session = context.app.session_manager.session()

    organisations_count = session.execute("select count(*) from organisations")
    if organisations_count.scalar() != 1:
        return False

    notices_count = session.execute("select count(*) from official_notices")
    if notices_count.scalar() != 0:
        return False

    context.operations.drop_table("official_notices")
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

    def is_already_updated(people_item: 'Sequence[Any]') -> bool:
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
                if file and not file.type == 'directory':
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
            news.hashtags = news.es_tags or []
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

    def is_already_updated(people_item: 'Sequence[Any]') -> bool:
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

    def is_broken(people_item: 'Sequence[Any]') -> bool:
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
