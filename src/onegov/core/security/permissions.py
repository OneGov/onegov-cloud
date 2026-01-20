""" OneGov uses a very simple permissions model by default. There are no
read/write permissions, just intents. That means a permission shows the
intended audience.

This is the default however, any application building on top of onegov.core
may of course introduce its own byzantine permission system.

"""
from __future__ import annotations


class Intent:
    """ Base class of all intents. Should never be used directly.
    This is only used for type checking.
    """


class Public(Intent):
    """ The general public is allowed to do this. """


class Private(Intent):
    """ Trusted people are allowed to do this. """


class Personal(Intent):
    """ Registered members are allowed to do this. """


class Secret(Intent):
    """ Only Demi-Gods are allowed to do this. """
