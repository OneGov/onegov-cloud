""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import itertools

from onegov.core.orm.types import JSON
from onegov.core.orm.types import UTCDateTime
from onegov.core.upgrade import upgrade_task
from onegov.people import Agency
from onegov.people import AgencyMembership
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text


@upgrade_task('Rename academic_title to salutation')
def rename_academic_title_to_salutation(context):

    context.operations.alter_column(
        'people', 'academic_title', new_column_name='salutation')


@upgrade_task('Add function column')
def add_function_column(context):
    context.operations.add_column(
        'people', Column('function', Text, nullable=True))


@upgrade_task('Add notes column')
def add_notes_column(context):
    context.operations.add_column(
        'people', Column('notes', Text, nullable=True))


@upgrade_task('Add quadratic picture url')
def add_person_quadratic_picture_url_column(context):
    if not context.has_column('people', 'quadratic_picture_url'):
        context.operations.add_column(
            'people', Column('quadratic_picture_url', Text, nullable=True))


@upgrade_task('Add person type column')
def add_person_type_column(context):
    if not context.has_column('people', 'type'):
        context.operations.add_column('people', Column('type', Text))


@upgrade_task('Add meta data and content columns')
def add_meta_data_and_content_columns(context):
    if not context.has_column('people', 'meta'):
        context.operations.add_column('people', Column('meta', JSON()))

    if not context.has_column('people', 'content'):
        context.operations.add_column('people', Column('content', JSON))


@upgrade_task('Add additional person columns')
def add_additional_person_columns(context):
    if not context.has_column('people', 'academic_title'):
        context.operations.add_column(
            'people',
            Column('academic_title', Text, nullable=True)
        )

    if not context.has_column('people', 'born'):
        context.operations.add_column(
            'people',
            Column('born', Text, nullable=True)
        )

    if not context.has_column('people', 'profession'):
        context.operations.add_column(
            'people',
            Column('profession', Text, nullable=True)
        )

    if not context.has_column('people', 'political_party'):
        context.operations.add_column(
            'people',
            Column('political_party', Text, nullable=True)
        )

    if not context.has_column('people', 'phone_direct'):
        context.operations.add_column(
            'people',
            Column('phone_direct', Text, nullable=True)
        )


@upgrade_task('Add parliamentary group column')
def add_parliamentary_group_column(context):
    if not context.has_column('people', 'parliamentary_group'):
        context.operations.add_column(
            'people',
            Column('parliamentary_group', Text, nullable=True)
        )


@upgrade_task('Rename order to order_within_agency')
def rename_order(context):
    context.operations.alter_column(
        'agency_memberships', 'order',
        new_column_name='order_within_agency')


@upgrade_task('Adding order_within_person column')
def add_order_within_person_column(context):
    from onegov.core.utils import normalize_for_url
    session = context.app.session()
    # Add the integer position based on alphabetic order

    def sortkey(result):
        return normalize_for_url(result[1])

    def groupkey(result):
        return result[0].person_id

    agency_list = []
    for result in session.query(
            AgencyMembership.id,
            AgencyMembership.agency_id,
            AgencyMembership.person_id,
    ):
        agency_list.append(result)

    title_list = []
    for result in agency_list:
        agency = session.query(Agency.id, Agency.title).filter_by(
            id=result.agency_id).one()
        title_list.append(agency.title)

    index_mapping = {}

    def get_index(agency_membership):
        return index_mapping[agency_membership.id]

    for person_id, memberships in itertools.groupby(
            zip(agency_list, title_list), key=groupkey):
        s_m = sorted(memberships, key=sortkey)
        for ix, membership in enumerate(s_m):
            index_mapping[membership[0].id] = ix

    if not context.has_column('agency_memberships', 'order_within_person'):
        context.add_column_with_defaults(
            'agency_memberships',
            Column('order_within_person', Integer, nullable=False),
            default=get_index
        )


@upgrade_task('Adds publication dates to agency models')
def add_publication_dates_to_agency_models(context):
    for table in ('agencies', 'agency_memberships', 'people'):
        for column in ('publication_start', 'publication_end'):
            if not context.has_column(table, column):
                context.operations.add_column(
                    table,
                    Column(column, UTCDateTime, nullable=True)
                )


@upgrade_task('Make people models polymorphic type non-nullable')
def make_people_models_polymorphic_type_non_nullable(context):
    for table in ('people', 'agency_memberships', 'agencies'):
        if context.has_table(table):
            context.operations.execute(f"""
                UPDATE {table} SET type = 'generic' WHERE type IS NULL;
            """)

            context.operations.alter_column(table, 'type', nullable=False)


@upgrade_task('Add address columns to agency')
def add_address_columns_to_agency(context):
    if not context.has_column('agencies', 'street'):
        context.operations.add_column('agencies', Column(
            'street', Text, nullable=True
        ))
    if not context.has_column('agencies', 'zip_code'):
        context.operations.add_column('agencies', Column(
            'zip_code', String(length=10), nullable=True
        ))
    if not context.has_column('agencies', 'city'):
        context.operations.add_column('agencies', Column(
            'city', Text, nullable=True
        ))


@upgrade_task(
    'Fix agency address column',
    requires='onegov.people:Add address columns to agency'
)
def fix_agency_address_column(context):
    if context.has_column('agencies', 'street'):
        context.operations.drop_column('agencies', 'street')
    if not context.has_column('agencies', 'address'):
        context.operations.add_column('agencies', Column(
            'address', Text, nullable=True
        ))


@upgrade_task(
    'Remove address columns from agency',
    requires='onegov.people:Fix agency address column'
)
def remove_address_columns_from_agency(context):
    if context.has_column('agencies', 'zip_code'):
        context.operations.drop_column('agencies', 'zip_code')
    if context.has_column('agencies', 'city'):
        context.operations.drop_column('agencies', 'city')
    if context.has_column('agencies', 'address'):
        context.operations.drop_column('agencies', 'address')
