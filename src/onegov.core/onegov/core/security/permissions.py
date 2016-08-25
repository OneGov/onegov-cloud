""" OneGov uses a very simple permissions model by default. There are no
read/write permissions, just intents. That means a permission shows the
intended audience.

This is the default however, any application building on top of onegov.core
may of course introduce its own byzantine permission system.

"""


class Public(object):
    """ The general public is allowed to do this. """


class Private(object):
    """ Trusted people are allowed to do this. """


class Personal(object):
    """ Registered members are allowed to do this. """


class Secret(object):
    """ Only Demi-Gods are allowed to do this. """
