from libres.context.registry import create_default_registry
from libres.db.models import ORMBase


class LibresIntegration(object):

    def configure_libres(self, **cfg):
        assert self.session_manager.bases, "Must be run after configure_dsn"
        self.session_manager.bases.append(ORMBase)

        self.libres_registry = create_default_registry()

        self.libres_context = self.libres_registry.register_context(
            'onegov.libres')

        self.libres_context.set_service(
            'session_provider', lambda ctx: self.session_manager)
