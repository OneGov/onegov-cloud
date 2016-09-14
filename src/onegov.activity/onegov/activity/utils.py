import string

from random import SystemRandom


GROUP_CODE_CHARS = string.ascii_uppercase + string.digits
GROUP_CODE_LENGTH = 10


def random_group_code():
    random = SystemRandom()

    return ''.join(
        random.choice(GROUP_CODE_CHARS)
        for _ in range(GROUP_CODE_LENGTH)
    )
