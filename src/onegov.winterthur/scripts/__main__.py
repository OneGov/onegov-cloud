import click

from .vollzug import transform_vollzug


@click.group()
def cli():
    pass


@cli.command(name='transform-vollzug')
@click.argument('path', type=click.Path(exists=True, file_okay=False))
@click.argument('prefix')
def transform_vollzug_cli(path, prefix):
    return transform_vollzug(path, prefix)


# run cli handler when running this thorugh pyhton -m
cli()
