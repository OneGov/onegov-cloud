""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import itertools
from onegov.core.orm.types import JSON
from onegov.core.upgrade import upgrade_task
from onegov.people import AgencyMembership, Agency
from sqlalchemy import Column, Integer
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
