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
    if not os.path.exists('node_modules'):
        os.system('yarn build')

    click.secho('Create a backup')
    shutil.move(foundation_src, foundation_bkp)
    shutil.move(js_file, js_file_bkp)

    click.secho('Copy files')
    shutil.copytree('node_modules/foundation-sites/_vendor', foundation_src)
    shutil.copytree('node_modules/foundation-sites/scss', foundation_src)

    shutil.copyfile('dist/assets/js/app.js', js_file)
    os.system('rm -rf /tmp/foundation-update')
    click.secho('Finished. Check differences in git now and run some tests',
                fg='green')
