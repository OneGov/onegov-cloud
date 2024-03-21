import operator
from email.headerregistry import Address
from markupsafe import Markup
from sqlalchemy import func

from onegov.core.mail import coerce_address
from onegov.people.models import Agency, Person


from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Iterator
    from datetime import datetime
    from onegov.agency.request import AgencyRequest
    from onegov.core.orm.mixins import TimestampMixin
    from onegov.user import RoleMapping
    from sqlalchemy.orm import Query
    from typing import TypeVar

    _T = TypeVar('_T')


# FIXME: Make this Markup aware
def handle_empty_p_tags(html: str) -> str:
    return html if not html == '<p></p>' else ''


def emails_for_new_ticket(
    model: Agency | Person,
    request: 'AgencyRequest'
) -> 'Iterator[Address]':
    """
    Returns an iterator with all the unique email addresses
    that need to be notified for a new ticket of this type
    """

    agencies: 'Iterable[Agency]'
    if isinstance(model, Agency):
        agencies = (model, )
        handler_code = 'AGN'
    elif isinstance(model, Person):
        agencies = (membership.agency for membership in model.memberships)
        handler_code = 'PER'
    else:
        raise NotImplementedError()

    seen = set()
    if request.email_for_new_tickets:
        # adding this to seen ensures it does not receive two emails
        address = coerce_address(request.email_for_new_tickets)
        seen.add(address.addr_spec)
        yield address

    # we need to match the access permission behavior of the tickets
    # so we can figure out if a group filter needs to be applied
    # we do this by getting the relevant list of groupids, if there
    # is no relevant list groupids will be None, and we don't need
    # to filter the groups at all.
    permissions = request.app.ticket_permissions.get(handler_code, {})
    if hasattr(model, 'group') and model.group in permissions:
        groupids: list[str] | None = permissions[model.group]
    else:
        groupids = permissions.get(None)

    # we try to minimize the amount of e-mail address parsing we
    # perform by de-duplicating the raw usernames as we get them
    role_mapping: 'RoleMapping'
    for agency in agencies:
        for role_mapping in getattr(agency, 'role_mappings', ()):
            if role_mapping.role != 'editor':
                continue

            # we only care about group role mappings
            group = role_mapping.group
            if group is None:
                continue

            # if the group does not have permission to manage this
            # type of ticket then we need to skip it
            if groupids is not None and group.id.hex not in groupids:
                continue

            # if the group does not have immediate notification
            # turned on, then skip it
            if not group.meta:
                continue
            if group.meta.get('immediate_notification') != 'yes':
                continue

            for user in group.users:
                # we already yielded this Address
                if user.username in seen:
                    continue

                seen.add(user.username)
                try:
                    yield Address(
                        display_name=user.realname or '',
                        addr_spec=user.username
                    )
                except ValueError:
                    # if it's not a valid address then skip it
                    pass


def get_html_paragraph_with_line_breaks(text: str | None) -> Markup:
    if not text:
        return Markup('')
    return Markup('<p>{}</p>').format(
        Markup('<br>').join(line for line in str(text).splitlines())
    )


def filter_modified_or_created(
    query: 'Query[_T]',
    relate: Literal['>', '<', '>=', '<=', '=='],
    # FIXME: This is a bit lax about types, SQLAlchemy is doing the heavy
    #        lifting here, auto casting ISO formatted date strings
    comparison_property: 'datetime | str',
    collection_class: type['TimestampMixin']
) -> 'Query[_T]':

    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
    }

    return query.filter(
        ops[relate](
            func.date_trunc('minute', collection_class.last_change),
            comparison_property
        )
    )
