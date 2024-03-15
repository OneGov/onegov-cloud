from onegov.core.security import Private
from onegov.org.views.allocation import (
    get_new_allocation_form_class, get_edit_allocation_form_class,
    get_allocation_rule_form_class, view_allocation_rules,
    handle_new_allocation, handle_edit_allocation, handle_allocation_rule)
from onegov.town6 import TownApp
from onegov.reservation import Allocation
from onegov.reservation import Resource
from onegov.town6.layout import (
    AllocationRulesLayout, ResourceLayout, AllocationEditFormLayout)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms import AllocationRuleForm
    from onegov.org.views.allocation import AllocationForm, AllocationEditForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(model=Resource, name='rules', permission=Private,
              template='allocation_rules.pt')
def town_view_allocation_rules(
    self: Resource,
    request: 'TownRequest'
) -> 'RenderData':
    return view_allocation_rules(
        self, request, AllocationRulesLayout(self, request))


@TownApp.form(model=Resource, template='form.pt', name='new-allocation',
              permission=Private, form=get_new_allocation_form_class)
def town_handle_new_allocation(
    self: Resource,
    request: 'TownRequest',
    form: 'AllocationForm'
) -> 'RenderData | Response':
    return handle_new_allocation(
        self, request, form, ResourceLayout(self, request))


@TownApp.form(model=Allocation, template='form.pt', name='edit',
              permission=Private, form=get_edit_allocation_form_class)
def town_handle_edit_allocation(
    self: Allocation,
    request: 'TownRequest',
    form: 'AllocationEditForm'
) -> 'RenderData | Response':
    """ Handles edit allocation for differing form classes. """

    return handle_edit_allocation(
        self, request, form, AllocationEditFormLayout(self, request))


@TownApp.form(model=Resource, template='form.pt', name='new-rule',
              permission=Private, form=get_allocation_rule_form_class)
def town_handle_allocation_rule(
    self: Resource,
    request: 'TownRequest',
    form: 'AllocationRuleForm'
) -> 'RenderData | Response':
    return handle_allocation_rule(
        self, request, form, AllocationRulesLayout(self, request))
