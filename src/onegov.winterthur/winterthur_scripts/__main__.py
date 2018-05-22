import click

from .fachstellen import transform_fachstellen
from .museum import transform_museum
from .rooms import transform_rooms
from .theater import transform_theater
from .vollzug import transform_vollzug


POST_MORTEM = False


@click.group()
@click.option('--pdb', default=False, is_flag=True)
def cli(pdb):
    global POST_MORTEM
    POST_MORTEM = pdb


@cli.command(name='transform-vollzug')
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('prefix')
@click.option('--output', type=click.Path(), default=None)
def transform_vollzug_cli(path, prefix, output):
    try:
        return transform_vollzug(path, prefix, output)
    except Exception:
        if POST_MORTEM:
            import pdb; pdb.post_mortem()  # noqa
        raise


@cli.command(name='transform-fachstellen')
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('prefix')
@click.option('--output', type=click.Path(), default=None)
def transform_fachstellen_cli(path, prefix, output):
    try:
        return transform_fachstellen(path, prefix, output)
    except Exception:
        if POST_MORTEM:
            import pdb; pdb.post_mortem()  # noqa
        raise


@cli.command(name='transform-museum')
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('prefix')
@click.option('--output', type=click.Path(), default=None)
def transform_museum_cli(path, prefix, output):
    try:
        return transform_museum(path, prefix, output)
    except Exception:
        if POST_MORTEM:
            import pdb; pdb.post_mortem()  # noqa
        raise


@cli.command(name='transform-rooms')
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('prefix')
@click.option('--output', type=click.Path(), default=None)
def transform_rooms_cli(path, prefix, output):
    try:
        return transform_rooms(path, prefix, output)
    except Exception:
        if POST_MORTEM:
            import pdb; pdb.post_mortem()  # noqa
        raise


@cli.command(name='transform-theater')
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('prefix')
@click.option('--output', type=click.Path(), default=None)
def transform_theater_cli(path, prefix, output):
    try:
        return transform_theater(path, prefix, output)
    except Exception:
        if POST_MORTEM:
            import pdb; pdb.post_mortem()  # noqa
        raise


# run cli handler when running this thorugh pyhton -m
cli()
