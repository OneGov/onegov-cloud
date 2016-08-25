from onegov.org import initial_content


# XXX compatibility shim for onegov.onboarding
def add_initial_content(*args, **kwargs):
    initial_content.add_initial_content(*args, **kwargs)
