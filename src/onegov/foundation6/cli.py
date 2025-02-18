from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
import click
from subprocess import check_output
from onegov.core.cli import command_group
from onegov.core.utils import module_path

cli = command_group()


def pre_checks() -> None:
    node_version = check_output('node --version', shell=True)  # nosec
    if 'v10' not in node_version.decode('utf-8'):
        click.secho('Foundation CLI currently works with node version 10')
        sys.exit()

    if not shutil.which('npm'):
        click.secho('Install npm package manager')
        sys.exit()

    if not shutil.which('foundation'):
        click.secho('Install foundation cli first: '
                    'npm install -g foundation-cli')
        sys.exit()


@cli.command(context_settings={
    'matches_required': False,
    'default_selector': '*'
})
def update() -> None:
    """ Update helper for foundation6 using node and webpack.
    By the time this cli is used, probabely things already changed and
    it needs to be adapted.
    Also some import might not work and have to be adapted manually.
    The Backup files can always be consulted.
    """

    pre_checks()
    module = Path(module_path('onegov.foundation6', 'foundation')).parent
    assets = module / 'assets'
    src = module / 'foundation'
    vendor_src = module / 'foundation' / 'vendor'
    # src_bckp = module / 'foundation.bak'

    for p in (src, vendor_src, assets):
        assert p.is_dir(), str(p)

    foundation_js_files = ('foundation.min.js', 'foundation.js')

    os.chdir('/tmp')  # nosec:B108
    if not os.path.exists('/tmp/foundation-update'):  # nosec:B108
        os.system(  # nosec
            'echo foundation-update | '
            'foundation new --framework sites --template zurb'
        )

    os.chdir('foundation-update')
    node_root = Path('/tmp/foundation-update/node_modules/foundation-sites')  # nosec:B108

    # click.secho('Create a backup', fg='green')
    # shutil.copytree(src, src_bckp)

    for name in ('scss', '_vendor'):
        click.secho(f'Copy {name} files')
        dest_ = src / 'foundation' / name
        src_ = node_root / name

        assert src_.is_dir(), str(src_)
        assert dest_.is_dir(), str(dest_)
        shutil.copytree(src_, dest_, dirs_exist_ok=True)

    click.secho('Copy foundation js files')
    for name in foundation_js_files:
        shutil.copyfile(
            node_root / 'dist' / 'js' / name,
            assets / name
        )

    click.secho('Copy motion-ui files')
    mui_src = node_root.parent / 'motion-ui' / 'src'
    assert mui_src.is_dir()
    mui_dest = vendor_src / 'motion-ui'
    assert mui_dest.is_dir()
    shutil.copytree(mui_src, mui_dest, dirs_exist_ok=True)

    click.secho('Run git add . to be sure everything is checked in.')
    click.secho('To roll back the changes, just use the power of git!')
    click.secho('Finished.', fg='green')
