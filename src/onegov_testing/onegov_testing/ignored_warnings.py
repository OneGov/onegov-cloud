""" Our tests hit on a lot of warnings, a lot of which are not useful. This
module configures the warnings hidden during testing.

"""

import warnings


def ignore(message, module):
    warnings.filterwarnings("ignore")


ignore("inspect.getargspec() is deprecated", module="reg")
