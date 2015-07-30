from libres.context.registry import create_default_registry
from libres.db.models import ORMBase


class LibresIntegration(object):
    """ Provides libres integration for
    :class:`onegov.core.framework.Framework` based applications.

    The application must be connected to a database

    Usage::

        from onegov.core import Framework

        class MyApp(Framework, LibresIntegration):
            pass

    """

    def configure_libres(self, **cfg):
        """ Configures the libres integration and leaves two properties on
        the class:

        :libres_context:
            The libres context configured for the current application.

        :libres_registrye:
            The libres registry bound to the current application.

        With those two a scheduler can easily be created::

            from libres import new_scheduler
            scheduler = new_scheduler(
                app.libres_context, 'test', 'Europe/Zurich'
            )

        """

        assert self.session_manager.bases, "Must be run after configure_dsn"
        self.session_manager.bases.append(ORMBase)

        self.libres_registry = create_default_registry()

        self.libres_context = self.libres_registry.register_context(
            'onegov.libres')

        self.libres_context.set_service(
            'session_provider', lambda ctx: self.session_manager)
