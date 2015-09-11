try:
    from queue import Queue, Full
except ImportError:
    from Queue import Queue, Full  # pragma: nocoverage # noqa
