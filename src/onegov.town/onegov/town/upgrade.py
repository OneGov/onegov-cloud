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


@upgrade_task('Install updated homepage structure')
def install_updated_homepage_structure(context):

    org = context.session.query(Organisation).first()

    if org is None:
        return

    # not a town
    if '<services />' not in org.meta['homepage_structure']:
        return

    org.meta['homepage_structure'] = textwrap.dedent("""\
        <row>
            <column span="12">
                <slider />
            </column>
        </row>
        <row>
            <column span="8">
                <row>
                    <column span="6">
                        <news />
                    </column>
                    <column span="6">
                        <events />
                    </column>
                </row>
                <line />
                <homepage-tiles />
            </column>
            <column span="4">
                <panel>
                    <services />
                </panel>
                <panel>
                    <directories />
                </panel>
            </column>
        </row>
    """)
