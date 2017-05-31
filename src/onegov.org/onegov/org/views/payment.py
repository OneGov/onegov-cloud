from onegov.core.security import Private
from onegov.org import OrgApp
from onegov.pay import Payment


@OrgApp.view(
    model=Payment,
    name='mark-as-paid',
    request_method='POST',
    permission=Private)
def mark_as_paid(self, request):
    request.assert_valid_csrf_token()

    assert self.source == 'manual'
    self.state = 'paid'


@OrgApp.view(
    model=Payment,
    name='mark-as-unpaid',
    request_method='POST',
    permission=Private)
def mark_as_unpaid(self, request):
    request.assert_valid_csrf_token()

    assert self.source == 'manual'
    self.state = 'open'
