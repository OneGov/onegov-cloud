import os
import shutil
import sys

import click

from onegov.core.cli import command_group
from onegov.core.utils import module_path

cli = command_group()


@cli.command(context_settings={
    'matches_required': False,
    'default_selector': '*'
})
def update():
    """ Update helper for foundation6 using node and webpack """
    if not shutil.which('foundation'):
        click.secho('Install foundation cli first')
        sys.exit()

    if not shutil.which('yarn'):
        click.secho('Install yarn package manager')
        sys.exit()

    os.chdir('/tmp')
    click.secho('Create dummy foundation project', fg='green')
    os.system(
        'echo foundation-update | '
        'foundation new --framework sites --template zurb'
    )
    os.chdir('foundation-update')
    os.system('yarn build')
    click.secho('Copy scss and bundled javascript', fg='green')
    shutil.copy('node_modules/foundation_sites/scss',
                module_path('onegov.foundation6', 'foundation/foundation'))
    shutil.copy('test-pr/dist/assets/js/app.js',
                module_path('onegov.foundation6', 'precompiled'))
    os.system('rm -rf foundation-update')
    click.secho('Finished. Check differences in git now and run some tests',
                fg='green')
