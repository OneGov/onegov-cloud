try:
    from queue import Queue, Empty, Full
except ImportError:
    from Queue import Queue, Empty, Full  # pragma: nocoverage # noqa
