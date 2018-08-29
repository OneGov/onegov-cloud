import click

from onegov.core.cli import abort
from onegov.core.cli import command_group
from onegov.core.cli import pass_group_context
from onegov.swissvotes import _
from onegov.swissvotes.models import TranslatablePage
from sqlalchemy import create_engine


cli = command_group()


@cli.command(context_settings={'creates_path': True})
@pass_group_context
def add(group_context):
    """ Adds an instance to the database. For example:

        onegov-swissvotes --select '/onegov_swissvotes/swissvotes' add

    """

    def add_instance(request, app):
        app.cache.invalidate()

        translators = {
            locale: app.translations.get(locale) for locale in app.locales
        }
        session = app.session()
        for page, title in (
            ('home', _("Homepage")),
            ('dataset', _("Dataset")),
            ('about', _("About")),
            ('contact', _("Contact")),
            ('disclaimer', _("Disclaimer")),
            ('imprint', _("Imprint")),
        ):
            translations = {
                locale: title.interpolate(translators[locale].gettext(title))
                for locale in app.locales
            }
            session.add(
                TranslatablePage(
                    id=page,
                    title_translations=translations,
                    content_translations=translations
                )
            )

        click.echo("Instance was created successfully")

    return add_instance


@cli.command()
@pass_group_context
def delete(group_context):
    """ Deletes an instance from the database. For example:

        onegov-swissvotes --select '/onegov_swissvotes/swissvotes' delete

    """

    def delete_instance(request, app):

        confirmation = "Do you really want to DELETE {}?".format(app.schema)

        if not click.confirm(confirmation):
            abort("Deletion process aborted")

        assert app.has_database_connection
        assert app.session_manager.is_valid_schema(app.schema)

        dsn = app.session_manager.dsn
        app.session_manager.session().close_all()
        app.session_manager.dispose()

        engine = create_engine(dsn)
        engine.execute('DROP SCHEMA "{}" CASCADE'.format(app.schema))
        engine.raw_connection().invalidate()
        engine.dispose()

        click.echo("Instance was deleted successfully")

    return delete_instance
