from __future__ import annotations

import morepath

from datetime import timedelta
from libres.db.models import ReservedSlot
from libres.modules.errors import LibresError

from onegov.core.security import Public, Private, Secret
from onegov.core.utils import is_uuid
from onegov.form import merge_forms
from onegov.org import OrgApp, utils, _
from onegov.org.forms import AllocationRuleForm
from onegov.org.forms import DaypassAllocationEditForm
from onegov.org.forms import DaypassAllocationForm
from onegov.org.forms import RoomAllocationEditForm
from onegov.org.forms import RoomAllocationForm
from onegov.org.forms.allocation import (
    DailyItemAllocationForm, DailyItemAllocationEditForm)
from onegov.org.layout import AllocationEditFormLayout
from onegov.org.layout import AllocationRulesLayout
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.reservation import Allocation
from onegov.reservation import Reservation
from onegov.reservation import Resource
from onegov.reservation import ResourceCollection
from purl import URL
from sedate import utcnow
from sqlalchemy import or_, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import defer, defaultload
from uuid import uuid4
from webob import exc


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.request import OrgRequest
    from sqlalchemy.orm import Query
    from typing import TypeAlias
    from webob import Response

    AllocationForm: TypeAlias = (
        DaypassAllocationForm
        | RoomAllocationForm
        | DailyItemAllocationForm
    )
    AllocationEditForm: TypeAlias = (
        DaypassAllocationEditForm
        | RoomAllocationEditForm
        | DailyItemAllocationEditForm
    )


@OrgApp.json(model=Resource, name='slots', permission=Public)
def view_allocations_json(self: Resource, request: OrgRequest) -> JSON_ro:
    """ Returns the allocations in a fullcalendar compatible events feed.

    See `<https://fullcalendar.io/docs/event_data/events_json_feed/>`_ for
    more information.

    """

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if not (start and end):
        return ()

    # get all allocations (including mirrors), for the availability calculation
    query: Query[Allocation]
    query = self.scheduler.allocations_in_range(  # type:ignore[assignment]
        start, end, masters_only=False)
    query = query.order_by(Allocation._start)
    query = query.options(defer(Allocation.data))
    query = query.options(defer(Allocation.group))
    query = query.options(
        defaultload('reserved_slots')
        .defer('reservation_token')
        .defer('allocation_id')
        .defer('end'))

    # but only return the master allocations
    return tuple(
        e.as_dict() for e in utils.AllocationEventInfo.from_allocations(
            request, self, tuple(query)
        )
    )


@OrgApp.view(model=Resource, name='process-rules', permission=Secret)
def process_rules(self: Resource, request: OrgRequest) -> None:
    """ Manually runs the rules processing cronjobs for testing.

    Not really dangerous, though it should be replaced with something
    proper instead, cronjobs currently do not run in most tests and that
    should be remedied.

    """

    if request.current_username == 'admin@example.org':
        handle_rules_cronjob(self, request)


@OrgApp.html(model=Resource, name='rules', permission=Private,
             template='allocation_rules.pt')
def view_allocation_rules(
    self: Resource,
    request: OrgRequest,
    layout: AllocationRulesLayout | None = None
) -> RenderData:

    layout = layout or AllocationRulesLayout(self, request)

    def link_for_rule(rule: dict[str, Any], name: str) -> str:
        url = URL(request.link(self, name))
        url = url.query_param('csrf-token', layout.csrf_token)
        url = url.query_param('rule', rule['id'])

        return url.as_string()

    def actions_for_rule(rule: dict[str, Any]) -> Iterator[Link]:
        yield Link(
            text=_('Stop'),
            url=link_for_rule(rule, 'stop-rule'),
            traits=(
                Confirm(
                    _(
                        'Do you really want to stop "${title}"?',
                        mapping={'title': rule['title']}
                    ),
                    _(
                        'The availability period will be removed without '
                        'affecting existing allocations.'
                    ),
                    _('Stop availability period'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=request.link(self, 'rules')
                )
            )
        )

        yield Link(
            text=_('Delete'),
            url=link_for_rule(rule, 'delete-rule'),
            traits=(
                Confirm(
                    _(
                        'Do you really want to delete "${title}"?',
                        mapping={'title': rule['title']}
                    ),
                    _(
                        "All allocations created by the availability period "
                        "will be removed, if they haven't been reserved yet."
                    ),
                    _('Delete availability period'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='POST',
                    redirect_after=request.link(self, 'rules')
                )
            )
        )
        yield Link(
            text=_('Edit'),
            url=link_for_rule(rule, 'edit-rule'),
        )

        yield Link(
            text=_('Copy'),
            url=link_for_rule(rule, 'copy-rule'),
            traits=(
                Intercooler(
                    request_method='POST',
                    redirect_after=request.link(self, 'rules')
                ),
            )
        )

    def rules_with_actions() -> Iterator[RenderData]:
        form_class = get_allocation_rule_form_class(self, request)

        for rule in self.content.get('rules', ()):
            form = request.get_form(form_class, csrf_support=False, model=self)
            form.rule = rule

            yield {
                'title': rule['title'],
                'actions': tuple(actions_for_rule(rule)),
                'form': form
            }

    return {
        'layout': layout,
        'title': _('Availability periods'),
        'rules': tuple(rules_with_actions())
    }


def get_new_allocation_form_class(
    resource: Resource,
    request: OrgRequest
) -> type[AllocationForm]:
    """ Returns the form class for new allocations (different resources have
    different allocation forms).

    """

    if resource.type == 'daypass':
        return DaypassAllocationForm

    if resource.type == 'room':
        return RoomAllocationForm

    if resource.type == 'daily-item':
        return DailyItemAllocationForm

    raise NotImplementedError


def get_edit_allocation_form_class(
    allocation: Allocation,
    request: OrgRequest
) -> type[AllocationEditForm]:
    """ Returns the form class for existing allocations (different resources
    have different allocation forms).

    """

    resource = ResourceCollection(
        request.app.libres_context).by_id(allocation.resource)
    assert resource is not None

    if resource.type == 'daypass':
        return DaypassAllocationEditForm

    if resource.type == 'room':
        return RoomAllocationEditForm

    if resource.type == 'daily-item':
        return DailyItemAllocationEditForm

    raise NotImplementedError


# NOTE: We would like the return type to be an intersection
def get_allocation_rule_form_class(
    resource: Resource,
    request: OrgRequest
) -> type[AllocationRuleForm]:
    """ Returns the form class for allocation rules. """

    form = get_new_allocation_form_class(resource, request)

    return merge_forms(AllocationRuleForm, form)


@OrgApp.form(model=Allocation, template='form.pt', name='edit',
             permission=Private, form=get_edit_allocation_form_class)
def handle_edit_allocation(
    self: Allocation,
    request: OrgRequest,
    form: AllocationEditForm,
    layout: AllocationEditFormLayout | None = None
) -> RenderData | Response:
    """ Handles edit allocation for differing form classes. """

    resources = ResourceCollection(request.app.libres_context)
    resource = resources.by_id(self.resource)
    assert resource is not None

    # this is a bit of a hack to keep the current view when a user drags an
    # allocation around, which opens this form and later leads back to the
    # calendar - if the user does this on the day view we want to return to
    # the same day view after the process
    # therefore we set the view on the resource (where this is okay) and on
    # the form action (where it's a bit of a hack), to ensure that the view
    # parameter is around for the whole time
    if isinstance(view := request.params.get('view'), str):
        resource.view = view
        assert hasattr(form, 'action')
        form.action = URL(form.action).query_param('view', view).as_string()

    if form.submitted(request):
        new_start, new_end = form.dates

        try:
            resource.scheduler.move_allocation(
                master_id=self.id,
                new_start=new_start,
                new_end=new_end,
                new_quota=form.quota,
                quota_limit=form.quota_limit,
                whole_day=form.whole_day
            )
        except LibresError as e:
            utils.show_libres_error(e, request)
        else:
            # when we edit an allocation, we disassociate it from any rules
            if self.data and 'rule' in self.data:
                self.data = {k: v for k, v in self.data.items() if k != 'rule'}

            request.success(_('Your changes were saved'))
            resource.highlight_allocations([self])

            return morepath.redirect(request.link(resource))
    elif not request.POST:
        form.apply_model(self)

        assert self.timezone is not None
        start, end = utils.parse_fullcalendar_request(request, self.timezone)
        if start and end:
            form.apply_dates(start, end)

    layout = layout or AllocationEditFormLayout(self, request)
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('Edit allocation'),
        'form': form
    }


@OrgApp.view(model=Allocation, request_method='DELETE', permission=Private)
def handle_delete_allocation(self: Allocation, request: OrgRequest) -> None:
    """ Deletes the given resource (throwing an error if there are existing
    reservations associated with it).

    """
    request.assert_valid_csrf_token()

    resource = request.app.libres_resources.by_allocation(self)
    assert resource is not None
    resource.scheduler.remove_allocation(id=self.id)

    @request.after
    def trigger_calendar_update(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'rc-allocations-changed')


@OrgApp.form(model=Resource, template='form.pt', name='new-rule',
             permission=Private, form=get_allocation_rule_form_class)
def handle_allocation_rule(
    self: Resource,
    request: OrgRequest,
    form: AllocationRuleForm,
    layout: AllocationRulesLayout | None = None
) -> RenderData | Response:

    layout = layout or AllocationRulesLayout(self, request)

    if form.submitted(request):
        changes = form.apply(self)

        rules = self.content.get('rules', [])
        rules.append(form.rule)
        self.content['rules'] = rules

        request.success(_(
            'New availability period active, ${n} allocations created',
            mapping={'n': changes}
        ))

        return request.redirect(request.link(self, name='rules'))

    elif not request.POST:
        start, end = utils.parse_fullcalendar_request(request, self.timezone)
        whole_day = request.params.get('whole_day') == 'yes'

        if start and end:
            if whole_day:
                form['start'].data = start
                form['end'].data = end

                if hasattr(form, 'as_whole_day'):
                    form.as_whole_day.data = 'yes'

            else:
                form['start'].data = start
                form['end'].data = end

                if hasattr(form, 'as_whole_day'):
                    form.as_whole_day.data = 'no'

                if hasattr(form, 'start_time'):
                    assert hasattr(form, 'end_time')
                    form.start_time.data = start
                    form.end_time.data = end

    return {
        'layout': layout,
        'title': _('New availabilty period'),
        'form': form,
        'helptext': _(
            'Availability periods ensure that the allocations between '
            'start/end exist and that they are extended beyond those dates at '
            'the given intervals.'
        )
    }


@OrgApp.form(model=Resource, template='form.pt', name='edit-rule',
             permission=Private, form=get_allocation_rule_form_class)
def handle_edit_rule(
    self: Resource, request: OrgRequest, form: AllocationRuleForm,
    layout: AllocationRulesLayout | None = None
) -> RenderData | Response:
    request.assert_valid_csrf_token()
    layout = layout or AllocationRulesLayout(self, request)

    rule_id = rule_id_from_request(request)

    if form.submitted(request):

        # all the slots
        slots = self.scheduler.managed_reserved_slots()
        slots = slots.with_entities(ReservedSlot.allocation_id)

        # all the reservations
        reservations = self.scheduler.managed_reservations()
        reservations = reservations.with_entities(Reservation.target)

        candidates = self.scheduler.managed_allocations()
        candidates = candidates.filter(
            func.json_extract_path_text(
                func.cast(Allocation.data, JSON), 'rule'
            ) == rule_id
        )
        # .. without the ones with slots
        deletable_candidates = candidates.filter(
            Allocation.id.notin_(slots.subquery()))

        # .. without the ones with reservations
        deletable_candidates = deletable_candidates.filter(
            Allocation.group.notin_(reservations.subquery()))

        # delete the allocations
        deleted_count = deletable_candidates.delete('fetch')

        # we need to update any undeletedable allocations with
        # the new rule_id and the new access
        updatable_candidates = candidates.filter(or_(
            Allocation.id.in_(slots.subquery()),
            Allocation.group.in_(reservations.subquery())
        ))

        # .. but only future ones (so we don't keep an ever-growing
        # rat's tail of ancient allocations we no longer care about)
        updatable_candidates = updatable_candidates.filter(
            Allocation._end >= utcnow())

        # update the allocations
        # NOTE: For now we only update the rule_id to keep the link
        #       as well as the access, everything else is left alone
        #       since it could otherwise result in inconsistent data
        new_data = {'rule': form.rule_id}
        if 'access' in form:
            new_data['access'] = form['access'].data

        # NOTE: This is a little bit dodgy, but since allocations aren't
        #       searchable and we don't have any other use-cases currently
        #       where we would want to know about changes to allocations
        #       the speed increase outweighs any future potential for
        #       bugs related to this bulk update
        with request.app.session_manager.ignore_bulk_updates():
            updated_count = updatable_candidates.update({
                Allocation.data: Allocation.data.op('||')(new_data)
            }, 'fetch')

        # Update the rule itself
        rules = self.content.get('rules', [])
        for i, rule in enumerate(rules):
            if rule['id'] == rule_id:
                updated_rule = form.rule
                updated_rule['last_run'] = utcnow()  # Reset last_run
                updated_rule['iteration'] = 0  # Reset iteration count
                rules[i] = updated_rule
                break
        self.content['rules'] = rules

        # Apply the updated rule
        new_allocations_count = form.apply(self)

        request.success(
            _(
                'Availability period updated. ${deleted} allocations removed, '
                '${updated} allocations adjusted and ${created} new '
                'allocations created.',
                mapping={
                    'deleted': deleted_count,
                    'updated': updated_count,
                    'created': new_allocations_count,
                },
            )
        )
        return request.redirect(request.link(self, name='rules'))

    # Pre-populate the form with existing rule data
    existing_rule = next(
        (
            rule
            for rule in self.content.get('rules', [])
            if rule['id'] == rule_id
        ),
        None,
    )
    if existing_rule is None:
        request.message(_('Availability period not found'), 'warning')
        return request.redirect(request.link(self, name='rules'))

    form.rule = existing_rule
    return {
        'layout': layout,
        'title': _('Edit availabilty period'),
        'form': form,
        'helptext': _(
            'Availability periods create availabilities between the specified '
            'start and end date. The availability period should ideally last '
            'until the next time the availabilities are expected to change. '
            'For example, a school term or a school year.'
        )
    }


def rule_id_from_request(request: OrgRequest) -> str:
    """ Returns the rule_id from the request params, ensuring that
    an actual uuid is returned.

    """
    rule_id = request.params.get('rule')

    if not isinstance(rule_id, str) or not is_uuid(rule_id):
        raise exc.HTTPBadRequest()

    return rule_id


def handle_rules_cronjob(resource: Resource, request: OrgRequest) -> None:
    """ Handles all cronjob duties of the rules stored on the given
    resource.

    """
    if not resource.content.get('rules'):
        return

    targets = []

    now = utcnow()
    tomorrow = (now + timedelta(days=1)).date()

    def should_process(rule: dict[str, Any]) -> bool:
        # do not reprocess rules if they were processed less than 12 hours
        # prior - this prevents flaky cronjobs from accidentally processing
        # rules too often
        if (
            rule['last_run']
            and rule['last_run'] > utcnow() - timedelta(hours=12)
        ):
            return False

        # we assume to be called once a day, so if we are called, a daily
        # rule has to be processed
        if rule['extend'] == 'daily':
            return True

        if rule['extend'] == 'monthly' and tomorrow.day == 1:
            return True

        if (
            rule['extend'] == 'yearly'
            and tomorrow.month == 1
            and tomorrow.day == 1
        ):
            return True

        return False

    def prepare_rule(rule: dict[str, Any]) -> dict[str, Any]:
        if should_process(rule):
            rule['iteration'] += 1
            rule['last_run'] = now

            targets.append(rule)

        return rule

    resource.content['rules'] = [
        prepare_rule(r) for r
        in resource.content.get('rules', ())]

    form_class = get_allocation_rule_form_class(resource, request)

    for rule in targets:
        form = request.get_form(form_class, csrf_support=False, model=resource)
        form.rule = rule
        form.apply(resource)


def delete_rule(resource: Resource, rule_id: str) -> None:
    """ Removes the given rule from the resource. """

    resource.content['rules'] = [
        rule for rule in resource.content.get('rules', ())
        if rule['id'] != rule_id
    ]


@OrgApp.view(model=Resource, request_method='POST', permission=Private,
             name='stop-rule')
def handle_stop_rule(self: Resource, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    rule_id = rule_id_from_request(request)
    delete_rule(self, rule_id)

    request.success(_('The availability period was stopped'))


@OrgApp.view(model=Resource, request_method='POST', permission=Private,
             name='copy-rule')
def handle_copy_rule(self: Resource, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    copied_rules: dict[str, dict[str, Any]]
    copied_rules = request.browser_session.get('copied_allocation_rules', {})

    rule_id = rule_id_from_request(request)
    for rule in self.content.get('rules', ()):
        if rule['id'] == rule_id:
            rule = rule.copy()
            rule['last_run'] = None
            rule['iteration'] = 0
            # NOTE: You can't copy between different resource types
            #       so we keep a separate copy per type
            copied_rules[self.type] = rule
            request.browser_session.copied_allocation_rules = copied_rules
            break
    else:
        raise exc.HTTPNotFound()

    request.success(_('The availability period was added to the clipboard'))


@OrgApp.view(model=Resource, request_method='POST', permission=Private,
             name='paste-rule')
def handle_paste_rule(self: Resource, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    copied_rules: dict[str, dict[str, Any]]
    copied_rules = request.browser_session.get('copied_allocation_rules', {})
    rule = copied_rules.get(self.type)
    if rule is None:
        raise exc.HTTPNotFound()

    form_class = get_allocation_rule_form_class(self, request)
    form = request.get_form(form_class, csrf_support=False, model=self)
    form.rule = rule
    # set a new uuid for the copy
    form.rule_id = uuid4().hex
    form.apply(self)

    rules = self.content.get('rules', [])
    rules.append(form.rule)
    self.content['rules'] = rules

    request.success(_('Pasted availability period from to the clipboard'))


@OrgApp.view(model=Resource, request_method='POST', permission=Private,
             name='delete-rule')
def handle_delete_rule(self: Resource, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    rule_id = rule_id_from_request(request)

    # all the slots
    slots = self.scheduler.managed_reserved_slots()
    slots = slots.with_entities(ReservedSlot.allocation_id)

    # all the reservations
    reservations = self.scheduler.managed_reservations()
    reservations = reservations.with_entities(Reservation.target)

    # include the allocations created by the given rule...
    candidates = self.scheduler.managed_allocations()
    candidates = candidates.filter(
        func.json_extract_path_text(
            func.cast(Allocation.data, JSON), 'rule'
        ) == rule_id
    )

    # .. without the ones with slots
    candidates = candidates.filter(
        Allocation.id.notin_(slots.subquery()))

    # .. without the ones with reservations
    candidates = candidates.filter(
        Allocation.group.notin_(reservations.subquery()))

    # delete the allocations
    count = candidates.delete('fetch')

    delete_rule(self, rule_id)

    request.success(
        _('The availability period was deleted, along with ${n} allocations',
          mapping={
            'n': count
        })
    )
