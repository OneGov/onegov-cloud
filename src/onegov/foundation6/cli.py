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
        click.secho('Install foundation cli first: '
                    'npm install -g foundation-cli')
        sys.exit()

    if not shutil.which('yarn'):
        click.secho('Install yarn package manager')
        sys.exit()

    foundation_src = module_path('onegov.foundation6', 'foundation/foundation')
    foundation_bkp = module_path(
        'onegov.foundation6', 'foundation/foundation.bak')
    foundation_js = module_path('onegov.foundation6', 'precompiled')
    js_name = 'foundation.min.js'
    js_file = os.path.join(foundation_js, js_name)
    js_file_bkp = os.path.join(foundation_js, js_name + '.bak')

    os.chdir('/tmp')
    if not os.path.exists('/tmp/foundation-update'):
        os.system(
            'echo foundation-update | '
            'foundation new --framework sites --template zurb'
        )

    os.chdir('foundation-update')

    click.secho('Create a backup', fg='green')
    shutil.move(foundation_src, foundation_bkp)
    if os.path.isfile(js_file):
        shutil.move(js_file, js_file_bkp)

    click.secho('Copy scss files')
    shutil.copytree('node_modules/foundation-sites/_vendor',
                    os.path.join(foundation_src, '_vendor'))
    shutil.copytree('node_modules/foundation-sites/scss',
                    os.path.join(foundation_src, 'scss'))

    click.secho('Bundle js file with gulp', fg='green')
    os.system('yarn build')

    shutil.copyfile('dist/assets/js/app.js', js_file)

    # Finally we move the _settings from scss/settings on level above since
    # otherwise the util import is wrong
    old_settings = os.path.join(
        foundation_src, 'scss', 'settings', '_settings.scss')
    if os.path.isfile(old_settings):
        shutil.move(old_settings, os.path.join(foundation_src, 'scss'))

    click.secho('Finished.', fg='green')
    click.secho('Remove .bak folder/file manually.', fg='green')
