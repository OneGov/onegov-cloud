from onegov.core.security import Private
from onegov.org.views.allocation import get_new_allocation_form_class, \
    get_edit_allocation_form_class, get_allocation_rule_form_class, \
    view_allocation_rules, handle_new_allocation, handle_edit_allocation, \
    handle_allocation_rule
from onegov.town6 import TownApp
from onegov.reservation import Allocation
from onegov.reservation import Resource
from onegov.town6.layout import AllocationRulesLayout, ResourceLayout, \
    AllocationEditFormLayout


@TownApp.html(model=Resource, name='rules', permission=Private,
              template='allocation_rules.pt')
def view_town_allocation_rules(self, request):
    return view_allocation_rules(
        self, request, AllocationRulesLayout(self, request))


@TownApp.form(model=Resource, template='form.pt', name='new-allocation',
              permission=Private, form=get_new_allocation_form_class)
def handle_town_new_allocation(self, request, form):
    return handle_new_allocation(
        self, request, form, ResourceLayout(self, request))


@TownApp.form(model=Allocation, template='form.pt', name='edit',
              permission=Private, form=get_edit_allocation_form_class)
def handle_town_edit_allocation(self, request, form):
    """ Handles edit allocation for differing form classes. """

    return handle_edit_allocation(
        self, request, form, AllocationEditFormLayout(self, request))


@TownApp.form(model=Resource, template='form.pt', name='new-rule',
              permission=Private, form=get_allocation_rule_form_class)
def handle_town_allocation_rule(self, request, form):
    return handle_allocation_rule(
        self, request, form, AllocationRulesLayout(self, request))
