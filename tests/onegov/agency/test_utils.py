from __future__ import annotations

from markupsafe import Markup
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson
from onegov.agency.utils import emails_for_new_ticket
from onegov.agency.utils import get_html_paragraph_with_line_breaks
from onegov.core.utils import Bunch
from onegov.ticket import TicketPermission
from onegov.user.models import RoleMapping
from onegov.user.models import User
from onegov.user.models import UserGroup


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from email.headerregistry import Address
    from onegov.agency import AgencyApp


# helper function to create an easier to check data structure
# from the output of emails_for_new_ticket
def condense(emails: Iterable[Address]) -> set[str]:
    result = set()
    for addr in emails:
        # make sure deduplication worked
        assert addr.addr_spec not in result
        result.add(addr.addr_spec)
    return result


def test_emails_for_new_ticket_AGN(agency_app: AgencyApp) -> None:
    session = agency_app.session()

    agency = ExtendedAgency(
        title="Test Agency",
        name="test-agency",
        portrait=Markup("This is a test\nagency.")
    )
    user_1 = User(
        username='user1@example.org',
        password_hash='password_hash',
        role='member'
    )
    user_2 = User(
        username='user2@example.org',
        password_hash='password_hash',
        role='member'
    )
    user_3 = User(
        username='user3@example.org',
        password_hash='password_hash',
        role='member'
    )
    group_1 = UserGroup(name='group1')
    group_2 = UserGroup(name='group2')
    session.add_all((agency, user_1, user_2, user_3, group_1, group_2))
    session.flush()

    user_1.groups = [group_1]
    user_2.groups = [group_1]
    user_3.groups = [group_2]

    request_1: Any = Bunch(
        app=agency_app,
        email_for_new_tickets=None
    )
    # this request has a notification email configured that happens
    # to match the email for user_1 to test deduplication
    request_2: Any = Bunch(
        app=agency_app,
        email_for_new_tickets='user1@example.org'
    )
    assert condense(emails_for_new_ticket(agency, request_1)) == set()
    assert condense(emails_for_new_ticket(agency, request_2)) == {
        'user1@example.org'
    }

    group_mapping = RoleMapping(
        group_id=group_1.id,
        content_type='agencies',
        content_id=str(agency.id),
        role='editor'
    )
    session.add(group_mapping)
    session.flush()

    # since the group does not have immediate_notifcation enabled
    # we still only get the email_for_new_tickets on the request
    assert condense(emails_for_new_ticket(agency, request_1)) == set()
    assert condense(emails_for_new_ticket(agency, request_2)) == {
        'user1@example.org'
    }

    group_1.meta = {'immediate_notification': 'yes'}
    # since no special ticket permission have been set for any
    # group this should now include everyone from group 1
    assert condense(emails_for_new_ticket(agency, request_1)) == {
        'user1@example.org', 'user2@example.org'
    }
    assert condense(emails_for_new_ticket(agency, request_2)) == {
        'user1@example.org', 'user2@example.org'
    }

    # but if we restrict AGN tickets to group 2 we should no
    # longer get the people from group 1, even though they are
    # in charge of this agency.
    ticket_permission = TicketPermission(
        handler_code='AGN',
        group=None,
        user_group=group_2
    )
    session.add(ticket_permission)
    session.flush()
    assert condense(emails_for_new_ticket(agency, request_1)) == set()
    assert condense(emails_for_new_ticket(agency, request_2)) == {
        'user1@example.org'
    }

    # lets also put group 2 in charge and enable immediate notifcation
    # for them
    group_2.meta = {'immediate_notification': 'yes'}
    group_mapping = RoleMapping(
        group_id=group_2.id,
        content_type='agencies',
        content_id=str(agency.id),
        role='editor'
    )
    session.add(group_mapping)
    session.flush()
    assert condense(emails_for_new_ticket(agency, request_1)) == {
        'user3@example.org'
    }
    assert condense(emails_for_new_ticket(agency, request_2)) == {
        'user1@example.org', 'user3@example.org'
    }


def test_emails_for_new_ticket_PER(agency_app: AgencyApp) -> None:
    session = agency_app.session()

    agency_1 = ExtendedAgency(
        title="Test Agency 1",
        name="test-agency-1",
        portrait=Markup("This is a test\nagency.")
    )
    agency_2 = ExtendedAgency(
        title="Test Agency 2",
        name="test-agency-2",
        portrait=Markup("This is a test\nagency.")
    )
    person = ExtendedPerson(
        first_name='A',
        last_name='Person'
    )
    user_1 = User(
        username='user1@example.org',
        password_hash='password_hash',
        role='member'
    )
    user_2 = User(
        username='user2@example.org',
        password_hash='password_hash',
        role='member'
    )
    group_1 = UserGroup(name='group1')
    group_2 = UserGroup(name='group2')
    session.add_all((
        agency_1, agency_2, person, user_1, user_2, group_1, group_2))
    session.flush()

    # we don't test all the permutations again, since a lot of it is
    # on shared code paths, so we turn on immediate notifications for
    # both user groups
    group_1.meta = {'immediate_notification': 'yes'}
    group_2.meta = {'immediate_notification': 'yes'}
    agency_1.add_person(person.id, "Staff", since="2012", note="N", prefix="*")
    agency_2.add_person(person.id, "Staff", since="2012", note="N", prefix="*")
    user_1.groups = [group_1]
    user_2.groups = [group_2]

    # we don't test email_for_new_tickets deduplication here too
    # since that is in the same code path for agencies, we instead
    # test deduplication between multiple agencies
    request: Any = Bunch(
        app=agency_app,
        email_for_new_tickets=None
    )
    assert condense(emails_for_new_ticket(person, request)) == set()

    group_mapping = RoleMapping(
        group_id=group_1.id,
        content_type='agencies',
        content_id=str(agency_1.id),
        role='editor'
    )
    session.add(group_mapping)
    session.flush()
    assert condense(emails_for_new_ticket(person, request)) == {
        'user1@example.org'
    }

    # but if we restrict AGN tickets to group 2 we should no
    # longer get the people from group 1, even though they are
    # in charge of this agency.
    ticket_permission = TicketPermission(
        handler_code='PER',
        group=None,
        user_group=group_2
    )
    session.add(ticket_permission)
    session.flush()
    assert condense(emails_for_new_ticket(person, request)) == set()

    group_mapping = RoleMapping(
        group_id=group_2.id,
        content_type='agencies',
        content_id=str(agency_1.id),
        role='editor'
    )
    session.add(group_mapping)
    session.flush()
    assert condense(emails_for_new_ticket(person, request)) == {
        'user2@example.org'
    }

    # lets put both groups in charge of agency 2 to test duplication
    # of user_2's email address
    group_mapping_1 = RoleMapping(
        group_id=group_1.id,
        content_type='agencies',
        content_id=str(agency_2.id),
        role='editor'
    )
    group_mapping_2 = RoleMapping(
        group_id=group_2.id,
        content_type='agencies',
        content_id=str(agency_2.id),
        role='editor'
    )
    session.add_all((group_mapping_1, group_mapping_2))
    session.flush()
    assert condense(emails_for_new_ticket(person, request)) == {
        'user2@example.org'
    }

    # lets also give PER permission to group_1
    ticket_permission = TicketPermission(
        handler_code='PER',
        group=None,
        user_group=group_1
    )
    session.add(ticket_permission)
    session.flush()
    assert condense(emails_for_new_ticket(person, request)) == {
        'user1@example.org', 'user2@example.org'
    }


def test_emails_for_new_ticket_parent_agency(agency_app: AgencyApp) -> None:
    session = agency_app.session()

    parent_agency = ExtendedAgency(
        title="Test Parent Agency",
        name="test-parent-agency",
        portrait=Markup("This is a test\nparent agency.")
    )
    agency = ExtendedAgency(
        title="Test Agency",
        name="test-agency",
        portrait=Markup("This is a test\nagency."),
    )
    user_1 = User(
        username='user1@example.org',
        password_hash='password_hash',
        role='member',
    )
    user_2 = User(
        username='user2@example.org',
        password_hash='password_hash',
        role='member',
    )
    user_3 = User(
        username='user3@example.org',
        password_hash='password_hash',
        role='member',
    )
    group_1 = UserGroup(name='group1')
    group_2 = UserGroup(name='group2')
    session.add_all(
        (parent_agency, agency, user_1, user_2, user_3, group_1, group_2)
    )
    session.flush()

    agency.parent = parent_agency
    group_1.meta = {'immediate_notification': 'yes'}
    group_2.meta = {'immediate_notification': 'yes'}
    user_1.groups = [group_1]
    user_2.groups = [group_1]
    user_3.groups = [group_2]

    request: Any = Bunch(
        app=agency_app,
        email_for_new_tickets=None
    )
    assert condense(emails_for_new_ticket(agency, request)) == set()

    group_mapping = RoleMapping(
        group_id=group_1.id,
        content_type='agencies',
        content_id=str(parent_agency.id),
        role='editor'
    )
    session.add(group_mapping)
    session.flush()

    # since no groups are mapped to agency, the tickets should
    # go to the group mapped to agency.parent instead
    assert condense(emails_for_new_ticket(agency, request)) == {
        'user1@example.org', 'user2@example.org'
    }

    # but if we map group 2 to the affected agency then
    # they should get the notification without the parent
    # agency being notified
    group_mapping = RoleMapping(
        group_id=group_2.id,
        content_type='agencies',
        content_id=str(agency.id),
        role='editor'
    )
    session.add(group_mapping)
    session.flush()
    assert condense(emails_for_new_ticket(agency, request)) == {
        'user3@example.org'
    }


def test_get_html_paragraph_with_line_breaks() -> None:
    assert get_html_paragraph_with_line_breaks(None) == ''
    assert get_html_paragraph_with_line_breaks('') == ''
    assert get_html_paragraph_with_line_breaks('Text') == '<p>Text</p>'
    assert get_html_paragraph_with_line_breaks(1) == '<p>1</p>'
    assert get_html_paragraph_with_line_breaks(
        '<script>alert("suprise!")</script>'
    ) == '<p>&lt;script&gt;alert(&#34;suprise!&#34;)&lt;/script&gt;</p>'
