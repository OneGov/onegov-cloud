from __future__ import annotations

import click
import gc
import os
import tracemalloc
from collections import deque
from operator import itemgetter


def current_memory_usage() -> int:
    import psutil  # only installed in development
    return psutil.Process(os.getpid()).memory_info().rss


class ResourceTracker:
    """ An object to track memory and other resources during development. """

    tracking_tools = (
        'tracemalloc.py',
        'linecache.py',
        'objgraph.py',
        'server/tracker.py'
    )

    memory_snapshots: deque[int]
    non_monotonic: set[str]
    tracebacks: dict[str, tuple[int, int]]

    def __init__(self, enable_tracemalloc: bool):
        self.memory_snapshots = deque(maxlen=10)

        self.non_monotonic = set()
        self.tracebacks = {}

        self.enable_tracemalloc = enable_tracemalloc
        self.started = False

        # get a baseline for memory, but not for the other things
        self.track_memory()

    def start(self) -> None:
        self.started = True

        if self.enable_tracemalloc:
            tracemalloc.start()

    @property
    def memory_snapshots_count(self) -> int:
        return self.memory_snapshots.maxlen  # type:ignore[return-value]

    @memory_snapshots_count.setter
    def memory_snapshots_count(self, value: int) -> None:
        # NOTE: We need to create a new deque to modify its size
        self.memory_snapshots = deque(self.memory_snapshots, maxlen=value)

    @property
    def memory_usage(self) -> int:
        return self.memory_snapshots[-1]

    @property
    def memory_usage_delta(self) -> int:
        if len(self.memory_snapshots) > 1:
            return self.memory_snapshots[-1] - self.memory_snapshots[-2]
        else:
            return self.memory_snapshots[-1]

    def track(self) -> None:
        if not self.started:
            self.start()

        self.track_memory()

        if tracemalloc.is_tracing():
            self.track_tracemalloc()

    def track_memory(self) -> None:
        self.memory_snapshots.append(current_memory_usage())

    def condense_name(self, name: str) -> str:
        if 'site-packages/' in name:
            return name.split('site-packages/', 1)[1]
        if 'src/' in name:
            return name.split('src/', 1)[1]

        return name

    def track_tracemalloc(self) -> None:
        # exclude debugging tools
        filters = tuple(
            tracemalloc.Filter(
                inclusive=False,
                filename_pattern=f'*{ex}*',
                all_frames=False
            ) for ex in (
                'tracemalloc.py',
                'linecache.py',
                'objgraph.py',
                'server/tracker.py'
            )
        )

        # removes noise
        gc.collect()

        snapshot = tracemalloc.take_snapshot().filter_traces(filters)
        statistics = snapshot.statistics('lineno')
        updated = set()

        for stat in statistics:

            name = f'{stat.traceback[0].filename}:{stat.traceback[0].lineno}'

            if name in self.non_monotonic:
                continue

            if name not in self.tracebacks:
                self.tracebacks[name] = (stat.size, 0)
                updated.add(name)
                continue

            size, stable_for = self.tracebacks[name]

            if size == stat.size:
                self.tracebacks[name] = (size, stable_for + 1)
                updated.add(name)
                continue

            if size > stat.size:
                self.non_monotonic.add(name)
                del self.tracebacks[name]
                continue

            if stat.size > size:
                self.tracebacks[name] = (stat.size, 0)
                updated.add(name)

        for name in self.tracebacks:
            if name not in updated:
                size, stable_for = self.tracebacks[name]
                self.tracebacks[name] = size, stable_for + 1

    def show_memory_usage(self) -> None:
        total = self.memory_usage / 1024 / 1024
        delta = self.memory_usage_delta / 1024 / 1024
        click.echo(f'Total memory used: {total:.3f}MiB ({delta:+.3f})')
        click.echo()

    def show_monotonically_increasing_traces(self) -> None:
        traces = [
            (n, info[0], info[1]) for n, info in self.tracebacks.items()
            if info[1] < 3  # unstable values only
        ]
        traces.sort(key=itemgetter(1), reverse=True)

        if not traces:
            click.echo('No montonically increasing traces')
            return

        click.echo(f'Monotonically increasing traces ({len(traces)}):')
        for name, size, stable_for in traces:
            if stable_for >= 3:
                continue

            name = self.condense_name(name)
            kib_size = size / 1024

            click.echo(f'{kib_size: >8.3f} KiB | {stable_for} | {name}')
        click.echo()
