from __future__ import annotations

from onegov.parliament.views.commission import (
    add_commission,
    delete_commission,
    edit_commission,
    view_commission,
    view_commissions,
)
from onegov.parliament.views.parliamentarian import (
    add_commission_membership,
    add_parliamentarian,
    delete_parliamentarian,
    edit_parliamentarian,
    view_parliamentarian,
    view_parliamentarians,
)
from onegov.parliament.views.parliamentary_group import (
    add_parliamentary_group,
    delete_parliamentary_group,
    edit_parliamentary_group,
    view_parliamentary_group,
    view_parliamentary_groups,
)


__all__ = (
    'add_commission',
    'delete_commission',
    'edit_commission',
    'view_commission',
    'view_commissions',
    'add_commission_membership',
    'add_parliamentarian',
    'delete_parliamentarian',
    'edit_parliamentarian',
    'view_parliamentarian',
    'view_parliamentarians',
    'add_parliamentary_group',
    'delete_parliamentary_group',
    'edit_parliamentary_group',
    'view_parliamentary_group',
    'view_parliamentary_groups',
)
