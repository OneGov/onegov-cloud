#: Describes the states which are visible to the given role (not taking
# ownership in account!)
from __future__ import annotations

VISIBLE_ACTIVITY_STATES = {
    'admin': (
        'preview',
        'proposed',
        'accepted',
        'archived'
    ),
    'editor': (
        'accepted',
    ),
    'member': (
        'accepted',
    ),
    'anonymous': (
        'accepted',
    )
}


#: Describes the states an owner editor can edit
OWNER_EDITABLE_STATES = ('preview', 'proposed')


#: Default donation amounts
DEFAULT_DONATION_AMOUNTS = (10, 30, 50)
