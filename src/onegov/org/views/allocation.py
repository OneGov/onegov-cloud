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
from onegov.org.layout import AllocationEditFormLayout
from onegov.org.layout import AllocationRulesLayout
from onegov.org.layout import ResourceLayout
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.reservation import Allocation
from onegov.reservation import Reservation
from onegov.reservation import Resource
from onegov.reservation import ResourceCollection
from purl import URL
from sedate import utcnow
from sqlalchemy import not_, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import defer, defaultload
from webob import exc


@OrgApp.json(model=Resource, name='slots', permission=Public)
def view_allocations_json(self, request):
    """ Returns the allocations in a fullcalendar compatible events feed.

    See `<http://fullcalendar.io/docs/event_data/events_json_feed/>`_ for
    more information.

    """

    start, end = utils.parse_fullcalendar_request(request, self.timezone)

    if not (start and end):
        return tuple()

    # get all allocations (including mirrors), for the availability calculation
    query = self.scheduler.allocations_in_range(start, end, masters_only=False)
    query = query.order_by(Allocation._start)
    query = query.options(defer(Allocation.data))
    query = query.options(defer(Allocation.group))
    query = query.options(
        defaultload('reserved_slots')
        .defer('reservation_token')
        .defer('allocation_id')
        .defer('end'))

    allocations = query.all()

    # but only return the master allocations
    return tuple(
        e.as_dict() for e in utils.AllocationEventInfo.from_allocations(
            request, self.scheduler, allocations
        )
    )


@OrgApp.view(model=Resource, name='process-rules', permission=Secret)
def process_rules(self, request):
    """ Manually runs the rules processing cronjobs for testing.

    Not really dangerous, though it should be replaced with something
    proper instead, cronjobs currently do not run in most tests and that
    should be remedied.

    """

    if request.current_username == 'admin@example.org':
        handle_rules_cronjob(self, request)


@OrgApp.html(model=Resource, name='rules', permission=Private,
             template='allocation_rules.pt')
def view_allocation_rules(self, request):
    layout = AllocationRulesLayout(self, request)

    def link_for_rule(rule, name):
        url = URL(request.link(self, name))
        url = url.query_param('csrf-token', layout.csrf_token)
        url = url.query_param('rule', rule['id'])

        return url.as_string()

    def actions_for_rule(rule):
        yield Link(
            text=_("Stop"),
            url=link_for_rule(rule, 'stop-rule'),
            traits=(
                Confirm(
                    _(
                        'Do you really want to stop "${title}"?',
                        mapping={'title': rule['title']}
                    ),
                    _(
                        "The rule will be removed without affecting "
                        "existing allocations."
                    ),
                    _("Stop rule"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method="POST",
                    redirect_after=request.link(self, 'rules')
                )
            )
        )

        yield Link(
            text=_("Delete"),
            url=link_for_rule(rule, 'delete-rule'),
            traits=(
                Confirm(
                    _(
                        'Do you really want to delete "${title}"?',
                        mapping={'title': rule['title']}
                    ),
                    _(
                        "All allocations created by the rule will be removed, "
                        "if they haven't been reserved yet."
                    ),
                    _("Delete rule"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method="POST",
                    redirect_after=request.link(self, 'rules')
                )
            )
        )

    def rules_with_actions():
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
        'title': _("Rules"),
        'rules': tuple(rules_with_actions())
    }


def get_new_allocation_form_class(resource, request):
    """ Returns the form class for new allocations (different resources have
    different allocation forms).

    """

    if resource.type == 'daypass':
        return DaypassAllocationForm

    if resource.type == 'room':
        return RoomAllocationForm

    raise NotImplementedError


def get_edit_allocation_form_class(allocation, request):
    """ Returns the form class for existing allocations (different resources
    have different allocation forms).

    """

    resource = ResourceCollection(
        request.app.libres_context).by_id(allocation.resource)

    if resource.type == 'daypass':
        return DaypassAllocationEditForm

    if resource.type == 'room':
        return RoomAllocationEditForm

    raise NotImplementedError


def get_allocation_rule_form_class(resource, request):
    """ Returns the form class for allocation rules. """

    form = get_new_allocation_form_class(resource, request)

    return merge_forms(AllocationRuleForm, form)


@OrgApp.form(model=Resource, template='form.pt', name='new-allocation',
             permission=Private, form=get_new_allocation_form_class)
def handle_new_allocation(self, request, form):
    """ Handles new allocations for differing form classes. """

    if form.submitted(request):
        try:
            allocations = self.scheduler.allocate(
                dates=form.dates,
                whole_day=form.whole_day,
                quota=form.quota,
                quota_limit=form.quota_limit,
                data=form.data,
                partly_available=form.partly_available
            )
        except LibresError as e:
            utils.show_libres_error(e, request)
        else:
            if not allocations:
                request.alert(_("No allocations to add"))
            else:
                request.success(
                    _("Successfully added ${n} allocations", mapping={
                        'n': len(allocations)
                    }))

                self.highlight_allocations(allocations)

                return morepath.redirect(request.link(self))

    elif not request.POST:
        start, end = utils.parse_fullcalendar_request(request, self.timezone)
        whole_day = request.params.get('whole_day') == 'yes'

        if start and end:
            if whole_day:
                form.start.data = start
                form.end.data = end

                if hasattr(form, 'as_whole_day'):
                    form.as_whole_day.data = 'yes'
            else:
                form.start.data = start
                form.end.data = end

                if hasattr(form, 'as_whole_day'):
                    form.as_whole_day.data = 'no'

                if hasattr(form, 'start_time'):
                    form.start_time.data = start
                    form.end_time.data = end

    layout = ResourceLayout(self, request)
    layout.breadcrumbs.append(Link(_("New allocation"), '#'))
    layout.editbar_links = None

    return {
        'layout': layout,
        'title': _("New allocation"),
        'form': form
    }


@OrgApp.form(model=Allocation, template='form.pt', name='edit',
             permission=Private, form=get_edit_allocation_form_class)
def handle_edit_allocation(self, request, form):
    """ Handles edit allocation for differing form classes. """

    resources = ResourceCollection(request.app.libres_context)
    resource = resources.by_id(self.resource)

    # this is a bit of a hack to keep the current view when a user drags an
    # allocation around, which opens this form and later leads back to the
    # calendar - if the user does this on the day view we want to return to
    # the same day view after the process
    # therefore we set the view on the resource (where this is okay) and on
    # the form action (where it's a bit of a hack), to ensure that the view
    # parameter is around for the whole time
    if 'view' in request.params:
        resource.view = view = request.params['view']
        form.action = URL(form.action).query_param('view', view).as_string()

    if form.submitted(request):
        new_start, new_end = form.dates

        try:
            resource.scheduler.move_allocation(
                master_id=self.id,
                new_start=new_start,
                new_end=new_end,
                new_quota=form.quota,
                quota_limit=form.quota_limit
            )
        except LibresError as e:
            utils.show_libres_error(e, request)
        else:
            # when we edit an allocation, we disassociate it from any rules
            if self.data and 'rule' in self.data:
                self.data = {k: v for k, v in self.data.items() if k != 'rule'}

            request.success(_("Your changes were saved"))
            resource.highlight_allocations([self])

            return morepath.redirect(request.link(resource))
    elif not request.POST:
        form.apply_model(self)

        start, end = utils.parse_fullcalendar_request(request, self.timezone)
        if start and end:
            form.apply_dates(start, end)

    return {
        'layout': AllocationEditFormLayout(self, request),
        'title': _("Edit allocation"),
        'form': form
    }


@OrgApp.view(model=Allocation, request_method='DELETE', permission=Private)
def handle_delete_allocation(self, request):
    """ Deletes the given resource (throwing an error if there are existing
    reservations associated with it).

    """
    request.assert_valid_csrf_token()

    resource = request.app.libres_resources.by_allocation(self)
    resource.scheduler.remove_allocation(id=self.id)

    @request.after
    def trigger_calendar_update(response):
        response.headers.add('X-IC-Trigger', 'rc-allocations-changed')


@OrgApp.form(model=Resource, template='form.pt', name='new-rule',
             permission=Private, form=get_allocation_rule_form_class)
def handle_allocation_rule(self, request, form):
    layout = AllocationRulesLayout(self, request)

    if form.submitted(request):
        changes = form.apply(self)

        rules = self.content.get('rules', [])
        rules.append(form.rule)
        self.content['rules'] = rules

        request.success(_(
            "New rule active, ${n} allocations created", mapping={'n': changes}
        ))

        return request.redirect(request.link(self, name='rules'))

    return {
        'layout': layout,
        'title': _("New Rule"),
        'form': form,
        'helptext': _(
            "Rules ensure that the allocations between start/end exist and "
            "that they are extended beyond those dates at the given "
            "intervals. "
        )
    }


def rule_id_from_request(request):
    """ Returns the rule_id from the request params, ensuring that
    an actual uuid is returned.

    """
    rule_id = request.params.get('rule')

    if not is_uuid(rule_id):
        raise exc.HTTPBadRequest()

    return rule_id


def handle_rules_cronjob(resource, request):
    """ Handles all cronjob duties of the rules stored on the given
    resource.

    """
    if not resource.content.get('rules'):
        return

    targets = []

    now = utcnow()
    tomorrow = (now + timedelta(days=1)).date()

    def should_process(rule):
        # do not reprocess rules if they were processed less than 12 hours
        # prior - this prevents flaky cronjobs from accidentally processing
        # rules too often
        if rule['last_run']\
                and rule['last_run'] > utcnow() - timedelta(hours=12):
            return False

        # we assume to be called once a day, so if we are called, a daily
        # rule has to be processed
        if rule['extend'] == 'daily':
            return True

        if rule['extend'] == 'monthly' and tomorrow.day == 1:
            return True

        if rule['extend'] == 'yearly'\
                and tomorrow.month == 1\
                and tomorrow.day == 1:

            return True

        return False

    def prepare_rule(rule):
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


def delete_rule(resource, rule_id):
    """ Removes the given rule from the resource. """

    resource.content['rules'] = [
        rule for rule in resource.content.get('rules', ())
        if rule['id'] != rule_id
    ]


@OrgApp.view(model=Resource, request_method='POST', permission=Private,
             name='stop-rule')
def handle_stop_rule(self, request):
    request.assert_valid_csrf_token()

    rule_id = rule_id_from_request(request)
    delete_rule(self, rule_id)

    request.success(_("The rule was stopped"))


@OrgApp.view(model=Resource, request_method='POST', permission=Private,
             name='delete-rule')
def handle_delete_rule(self, request):
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
        not_(Allocation.id.in_(slots.subquery())))

    # .. without the ones with reservations
    candidates = candidates.filter(
        not_(Allocation.group.in_(reservations.subquery())))

    # delete the allocations
    count = candidates.delete('fetch')

    delete_rule(self, rule_id)

    request.success(
        _("The rule was deleted, along with ${n} allocations", mapping={
            'n': count
        })
    )
