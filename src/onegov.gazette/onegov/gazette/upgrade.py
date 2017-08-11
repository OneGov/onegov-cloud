from onegov.core.upgrade import upgrade_task
from onegov.gazette.models import GazetteNotice


@upgrade_task('Moves organization and category IDs to meta')
def move_ids_to_meta(context):
    try:
        organizations = context.request.app.principal.organizations
        categories = context.request.app.principal.categories
    except AttributeError:
        pass
    else:
        for notice in context.session.query(GazetteNotice):
            if notice.organization in organizations:
                notice.organization_id = notice.organization
                notice.organization = organizations[notice.organization_id]
            if notice.category in categories:
                notice.category_id = notice.category
                notice.category = categories[notice.category_id]


@upgrade_task(
    'Set issue date',
    requires='onegov.notice:Adds an issue date column to the official notices'
)
def set_issue_date(context):
    try:
        context.request.app.principal.issues
    except AttributeError:
        pass
    else:
        for notice in context.session.query(GazetteNotice):
            if not notice.issue_date and notice.issues:
                notice.apply_meta(context.request.app.principal)
