""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.orm import Base, find_models
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from onegov.core.utils import normalize_for_url
from onegov.directory import DirectoryEntry
from onegov.directory.models.directory import DirectoryFile, Directory
from onegov.file import File
from onegov.form import FormDefinition
from onegov.org.models import Organisation, Topic, News, ExtendedDirectory
from onegov.org.utils import annotate_html
from onegov.page import Page
from onegov.reservation import Resource
from sqlalchemy.orm import undefer
from onegov.core.crypto import random_token
from lxml.html import fragments_fromstring


@upgrade_task('Move from town to organisation', always_run=True)
def move_town_to_organisation(context):

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


@upgrade_task('Add image-dimensions to html')
def add_image_dimensions_to_html(context):
    for topic in context.session.query(Topic):
        topic.text = annotate_html(topic.text, context.request)

    for news in context.session.query(News):
        news.text = annotate_html(news.text, context.request)

    for resource in context.session.query(Resource):
        resource.text = annotate_html(resource.text, context.request)

    for form in context.session.query(FormDefinition):
        form.text = annotate_html(form.text, context.request)


@upgrade_task('Remove official notices table')
def remove_official_notices_table(context):
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


@upgrade_task('Add new defaults to existing directories')
def add_new_defaults_to_existing_directories(context):
    for directory in context.session.query(ExtendedDirectory):
        directory.enable_submissions = False
        directory.price = 'free'
        directory.currency = 'CHF'


@upgrade_task('Migrate enable_map option')
def migrate_enable_map_option(context):
    for directory in context.session.query(ExtendedDirectory):
        directory.enable_map = directory.enable_map and 'everywhere' or 'no'


@upgrade_task('Fix directory order')
def fix_directory_order(context):
    for directory in context.session.query(ExtendedDirectory):
        directory.order = normalize_for_url(directory.title)


@upgrade_task('Add default redirect setting')
def add_default_recirect_setting(context):
    org = context.session.query(Organisation).first()

    if org:
        org.redirect_homepage_to = 'no'


@upgrade_task('Rename guideline to submissions_guideline')
def rename_guideline_to_submissions_guideline(context):
    directories = context.session.query(ExtendedDirectory)\
        .options(undefer(ExtendedDirectory.content))

    for directory in directories:
        directory.content['submissions_guideline'] \
            = directory.content.pop('guideline', None)


@upgrade_task('Add meta access property')
def add_meta_access_property(context):
    def has_meta_property(model):
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
def add_rerender_organsiation_html(context):
    org = context.session.query(Organisation).first()

    if not org:
        return

    if org.contact is not None:
        org.contact = org.contact

    if org.opening_hours is not None:
        org.opening_hours = org.opening_hours


@upgrade_task("Migrate FormFile's attached to DirectoryEntry to DirectoryFile")
def fix_directory_file_identity(context):
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
                    new = DirectoryFile(
                        id=random_token(),
                        name=file.name,
                        note=file.note,
                        reference=file.reference
                    )
                    entry.files.append(new)
                    entry.content['values'][field.id]['data'] = f'@{new.id}'
                    entry.content.changed()


@upgrade_task('Cache news hashtags in meta')
def cache_news_hashtags_in_meta(context):
    try:
        for news in context.session.query(News):
            news.hashtags = news.es_tags or []
    except Exception:
        pass


@upgrade_task('Migrate all html fields to editor js')
def upgrade_html_fields_to_editor_js(context):
    fields_to_model = {
        'text': [Resource, Directory, Page, FormDefinition],
        'homepage_cover': [Organisation],
        'submissions_guideline': [Directory],
        'change_requests_guideline': [Directory],
    }

    seen_tags = set()

    def migrate(html):
        if not html:
            return
        fragments = fragments_fromstring(html)
        for frag in fragments:
            seen_tags.add(frag.tag)

    session = context.session

    for attr, models in fields_to_model.items():
        for m in models:
            for item in session.query(m):
                migrate(getattr(item, attr))

    print(seen_tags)
    assert False
