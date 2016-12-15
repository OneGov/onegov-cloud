#: Describes the states which are visible to the given role (not taking
# ownership in account!)
VISIBLE_ACTIVITY_STATES = {
    'admin': (
        'preview',
        'proposed',
        'accepted',
        'denied',
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
