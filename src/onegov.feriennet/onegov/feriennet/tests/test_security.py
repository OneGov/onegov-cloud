from onegov.activity import ActivityCollection
from onegov.core.security import Public
from onegov.core.utils import Bunch
from onegov.feriennet.policy import ActivityQueryPolicy
from onegov.feriennet.security import has_public_permission_logged_in
from onegov.feriennet.security import has_public_permission_not_logged_in
from onegov.feriennet.security import is_owner
from onegov.user import UserCollection


def test_is_owner():
    assert not is_owner(username=None, activity=Bunch(username=None))
    assert is_owner(username='xy', activity=Bunch(username='xy'))


def test_activity_query_policy(session):
    UserCollection(session).add(
        username='Steven',
        password='hunter2',
        role='editor'
    )

    UserCollection(session).add(
        username='Leland',
        password='hunter2',
        role='editor'
    )

    collection = ActivityCollection(session)

    activities = [
        collection.add(
            title="Visit the Pet Cemetary",
            username="Steven"
        ),
        collection.add(
            title="Shop at Needful Things",
            username="Leland"
        )
    ]

    # admins see all
    policy = ActivityQueryPolicy("Steven", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("Leland", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    # owners see their own
    policy = ActivityQueryPolicy("Steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("Leland", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    # members only see accepted, even if they are the owner
    policy = ActivityQueryPolicy("Steven", 'member')
    assert policy.granted_subset(collection.query()).count() == 0

    policy = ActivityQueryPolicy("Leland", 'member')
    assert policy.granted_subset(collection.query()).count() == 0

    # proposed activites stay visible to owners but keep hidden from others
    activities[0].propose()

    policy = ActivityQueryPolicy("Steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("Leland", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    # once an activity is accepted, it becomes public
    activities[0].accept()

    policy = ActivityQueryPolicy("Steven", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("Steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("Steven", 'member')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy(None, None)
    assert policy.granted_subset(collection.query()).count() == 1

    # if an activity is denied, it remains visible to owners/editors
    # unless the owner is not an editor or admin
    activities[1].propose()
    activities[1].deny()

    policy = ActivityQueryPolicy("Leland", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("Leland", 'editor')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("Leland", 'member')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy(None, None)
    assert policy.granted_subset(collection.query()).count() == 1

    # if an activity is archived, it remains visible to owners/editors
    # unless the owner is not an editor or admin
    activities[0].archive()

    policy = ActivityQueryPolicy("Steven", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("Steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("Steven", 'member')
    assert policy.granted_subset(collection.query()).count() == 0

    policy = ActivityQueryPolicy(None, None)
    assert policy.granted_subset(collection.query()).count() == 0


def test_activity_permission_anonymous():

    def has_permission(state):
        return has_public_permission_not_logged_in(
            app=None,
            identity=None,
            model=Bunch(state=state),
            permission=Public
        )

    assert not has_permission('preview')
    assert not has_permission('proposed')
    assert has_permission('accepted')
    assert not has_permission('denied')
    assert not has_permission('archived')


def test_activity_permission():

    def has_permission(owner, user, role, state):
        return has_public_permission_logged_in(
            app=None,
            identity=Bunch(userid=user, role=role),
            model=Bunch(state=state, username=owner),
            permission=Public
        )

    # the owner has permission to the preview, if not member
    assert has_permission('owner', 'owner', 'admin', 'preview')
    assert has_permission('owner', 'owner', 'editor', 'preview')
    assert not has_permission('owner', 'owner', 'member', 'preview')

    # the admin sees all states
    assert has_permission('owner', 'user', 'admin', 'preview')
    assert has_permission('owner', 'user', 'admin', 'proposed')
    assert has_permission('owner', 'user', 'admin', 'accepted')
    assert has_permission('owner', 'user', 'admin', 'denied')
    assert has_permission('owner', 'user', 'admin', 'archived')

    # the owner has permission to all owned objects
    assert has_permission('owner', 'owner', 'admin', 'preview')
    assert has_permission('owner', 'owner', 'admin', 'proposed')
    assert has_permission('owner', 'owner', 'admin', 'accepted')
    assert has_permission('owner', 'owner', 'admin', 'denied')
    assert has_permission('owner', 'owner', 'admin', 'archived')

    assert has_permission('owner', 'owner', 'editor', 'preview')
    assert has_permission('owner', 'owner', 'editor', 'proposed')
    assert has_permission('owner', 'owner', 'editor', 'accepted')
    assert has_permission('owner', 'owner', 'editor', 'denied')
    assert has_permission('owner', 'owner', 'editor', 'archived')

    # ..unless the role is the one of a member (treated like anonymous)
    assert not has_permission('owner', 'owner', 'member', 'preview')
    assert not has_permission('owner', 'owner', 'member', 'proposed')
    assert has_permission('owner', 'owner', 'member', 'accepted')
    assert not has_permission('owner', 'owner', 'member', 'denied')
    assert not has_permission('owner', 'owner', 'member', 'archived')
