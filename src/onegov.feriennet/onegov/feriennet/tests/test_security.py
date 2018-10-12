from onegov.activity import ActivityCollection
from onegov.core.security import Public, Private
from onegov.core.utils import Bunch
from onegov.feriennet.policy import ActivityQueryPolicy
from onegov.feriennet.security import has_public_permission_logged_in
from onegov.feriennet.security import has_public_permission_not_logged_in
from onegov.feriennet.security import has_private_permission_activities
from onegov.feriennet.security import has_private_permission_occasions
from onegov.feriennet.security import is_owner


def test_is_owner():
    assert not is_owner(username=None, activity=Bunch(username=None))
    assert is_owner(username='xy', activity=Bunch(username='xy'))


def test_activity_query_policy(session, scenario):
    scenario.add_period()
    scenario.add_user(username='steven', password='hunter2', role='editor')
    scenario.add_user(username='leland', password='hunter2', role='editor')
    scenario.add_activity(title="Visit the Pet Cemetary", username='steven')
    scenario.add_activity(title="Shop at Needful Things", username='leland')
    scenario.commit()

    collection = ActivityCollection(session)

    # admins see all
    policy = ActivityQueryPolicy("steven", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("leland", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    # owners see their own
    policy = ActivityQueryPolicy("steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("leland", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    # members only see accepted, even if they are the owner
    policy = ActivityQueryPolicy("steven", 'member')
    assert policy.granted_subset(collection.query()).count() == 0

    policy = ActivityQueryPolicy("leland", 'member')
    assert policy.granted_subset(collection.query()).count() == 0

    # proposed activites stay visible to owners but keep hidden from others
    scenario.refresh()
    scenario.activities[0].propose()
    scenario.commit()

    policy = ActivityQueryPolicy("steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("leland", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    # once an activity is accepted, it becomes public
    scenario.refresh()
    scenario.activities[0].accept()
    scenario.commit()

    policy = ActivityQueryPolicy("steven", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("steven", 'member')
    assert policy.granted_subset(collection.query()).count() == 0

    policy = ActivityQueryPolicy(None, None)
    assert policy.granted_subset(collection.query()).count() == 0

    # but members only see it if there's at least one occasion
    scenario.refresh()
    scenario.add_occasion(activity=scenario.activities[0])
    scenario.commit()

    policy = ActivityQueryPolicy("steven", 'member')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy(None, None)
    assert policy.granted_subset(collection.query()).count() == 1

    # if an activity is archived, it remains visible to owners/editors
    # unless the owner is not an editor or admin
    scenario.refresh()
    scenario.activities[0].archive()
    scenario.commit()

    policy = ActivityQueryPolicy("steven", 'admin')
    assert policy.granted_subset(collection.query()).count() == 2

    policy = ActivityQueryPolicy("steven", 'editor')
    assert policy.granted_subset(collection.query()).count() == 1

    policy = ActivityQueryPolicy("steven", 'member')
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
    assert has_permission('owner', 'user', 'admin', 'archived')

    # the owner has permission to all owned objects
    assert has_permission('owner', 'owner', 'admin', 'preview')
    assert has_permission('owner', 'owner', 'admin', 'proposed')
    assert has_permission('owner', 'owner', 'admin', 'accepted')
    assert has_permission('owner', 'owner', 'admin', 'archived')

    assert has_permission('owner', 'owner', 'editor', 'preview')
    assert has_permission('owner', 'owner', 'editor', 'proposed')
    assert has_permission('owner', 'owner', 'editor', 'accepted')
    assert has_permission('owner', 'owner', 'editor', 'archived')

    # ..unless the role is the one of a member (treated like anonymous)
    assert not has_permission('owner', 'owner', 'member', 'preview')
    assert not has_permission('owner', 'owner', 'member', 'proposed')
    assert has_permission('owner', 'owner', 'member', 'accepted')
    assert not has_permission('owner', 'owner', 'member', 'archived')


def test_editor_permissions():

    def has_activity_permission(owner, user, role, state):
        return has_private_permission_activities(
            app=None,
            identity=Bunch(userid=user, role=role),
            model=Bunch(state=state, username=owner),
            permission=Private
        )

    def has_occasion_permission(owner, user, role, state):
        return has_private_permission_occasions(
            app=None,
            identity=Bunch(userid=user, role=role),
            model=Bunch(activity=Bunch(
                state=state,
                username=owner
            )),
            permission=Private
        )

    # editors only got rights if they are owners and the activity
    # is in the preview/proposed state
    assert has_activity_permission('owner', 'owner', 'editor', 'preview')
    assert has_activity_permission('owner', 'owner', 'editor', 'proposed')
    assert not has_activity_permission('owner', 'owner', 'editor', 'accepted')
    assert not has_activity_permission('owner', 'owner', 'editor', 'archived')

    assert has_occasion_permission('owner', 'owner', 'editor', 'preview')
    assert has_occasion_permission('owner', 'owner', 'editor', 'proposed')
    assert not has_occasion_permission('owner', 'owner', 'editor', 'accepted')
    assert not has_occasion_permission('owner', 'owner', 'editor', 'archived')
