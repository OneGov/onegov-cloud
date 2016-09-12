""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import textwrap

from onegov.core.upgrade import upgrade_task
from onegov.org.models import Organisation


@upgrade_task('Install the default homepage structure')
def install_default_homepage_structure(context):

    org = context.session.query(Organisation).first()

    if org is None:
        return

    org.meta['homepage_structure'] = textwrap.dedent("""\
        <row>
            <column span="8">
                <homepage-tiles />
                <news />
            </column>
            <column span="4">
                <panel>
                    <services />
                </panel>
                <panel>
                    <events />
                </panel>
                <panel>
                    <directories />
                </panel>
            </column>
        </row>
    """)
