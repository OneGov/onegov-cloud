from onegov.core.upgrade import upgrade_task
from sqlalchemy import Column
from sqlalchemy import Text
from onegov.notice.models import OfficialNotice


@upgrade_task('Adds a text column to the official notices')
def add_text_column(context):
    if not context.has_column('official_notices', 'text'):
        # Create the new row
        context.operations.add_column(
            'official_notices',
            Column('text', Text, nullable=True)
        )

        # Copy the data
        for notice in context.session.query(OfficialNotice):
            notice.text = notice.content.get('text', '')
            notice.content = {}


@upgrade_task('Adds a organization column to the official notices')
def add_organization_column(context):
    if not context.has_column('official_notices', 'organization'):
        context.operations.add_column(
            'official_notices',
            Column('organization', Text, nullable=True)
        )
