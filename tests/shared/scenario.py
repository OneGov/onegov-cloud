from contextlib import contextmanager

import transaction


class BaseScenario(object):

    def __init__(self, session, test_password):
        self.session = session
        self.test_password = test_password

    def __getattribute__(self, name):
        if name.startswith('add_') and not transaction.manager.manager._txn:
            transaction.begin()

        return super().__getattribute__(name)

    def commit(self):
        transaction.commit()

    @property
    def cached_attributes(self):
        raise NotImplementedError

    @contextmanager
    def update(self):
        self.refresh()
        yield
        self.commit()

    def add(self, model, **columns):
        obj = model(**columns)
        self.session.add(obj)

        return obj

    def refresh(self):
        transaction.begin()

        for name in self.cached_attributes:
            cache = getattr(self, name)

            for ix, item in enumerate(cache):
                cache[ix] = self.session.merge(item)
                self.session.refresh(cache[ix])
