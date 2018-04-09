import gc
import os
import tracemalloc


def current_memory_usage():
    import psutil  # only installed in development
    return psutil.Process(os.getpid()).memory_info().rss


class ResourceTracker(object):
    """ An object to track memory and other resources during development. """

    tracking_tools = (
        'tracemalloc.py',
        'linecache.py',
        'objgraph.py',
        'server/tracker.py'
    )

    def __init__(self, enable_tracemalloc):
        self.memory_snapshots = []
        self.memory_snapshots_count = 10

        self.non_monotonic = set()
        self.tracebacks = {}

        self.enable_tracemalloc = enable_tracemalloc
        self.started = False

        # get a baseline for memory, but not for the other things
        self.track_memory()

    def start(self):
        self.started = True

        if self.enable_tracemalloc:
            tracemalloc.start()

    @property
    def memory_usage(self):
        return self.memory_snapshots[-1]

    @property
    def memory_usage_delta(self):
        if len(self.memory_snapshots) > 1:
            return self.memory_snapshots[-1] - self.memory_snapshots[-2]
        else:
            return self.memory_snapshots[-1]

    def track(self):
        if not self.started:
            self.start()

        self.track_memory()

        if tracemalloc.is_tracing():
            self.track_tracemalloc()

    def track_memory(self):
        self.memory_snapshots.append(current_memory_usage())
        self.memory_snapshots = self.memory_snapshots[
            -self.memory_snapshots_count:
        ]

    def condense_name(self, name):
        if 'site-packages/' in name:
            return name.split('site-packages/', 1)[1]
        if 'src/' in name:
            return name.split('src/', 1)[1]

        return name

    def track_tracemalloc(self):
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

    def show_memory_usage(self):
        total = self.memory_usage / 1024 / 1024
        delta = self.memory_usage_delta / 1024 / 1024
        print(f"Total memory used: {total:.3f}MiB ({delta:+.3f})")
        print()

    def show_monotonically_increasing_traces(self):
        traces = [
            (n, info[0], info[1]) for n, info in self.tracebacks.items()
            if info[1] < 3  # unstable values only
        ]
        traces.sort(key=lambda item: item[1], reverse=True)

        if not traces:
            print("No montonically increasing traces")
            return

        print(f"Monotonically increasing traces ({len(traces)}):")
        for name, size, stable_for in traces:
            if stable_for >= 3:
                continue

            name = self.condense_name(name)
            size = size / 1024

            print(f"{size: >8.3f} KiB | {stable_for} | {name}")
        print()
