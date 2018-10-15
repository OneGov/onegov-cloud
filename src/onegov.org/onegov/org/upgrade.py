""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
from onegov.core.upgrade import upgrade_task
from onegov.core.utils import normalize_for_url
from onegov.form import FormDefinition
from onegov.org.models import Organisation, Topic, News, ExtendedDirectory
from onegov.org.utils import annotate_html
from onegov.reservation import Resource


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
