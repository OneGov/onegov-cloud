""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
import textwrap
from onegov.town6.theme.town_theme import MERRIWEATHER, ROBOTO_CONDENSED
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


@upgrade_task('Upgrade homepage structure to include directories')
def upgrade_homepage_structure_to_include_directories(context):
    org = context.session.query(Organisation).first()

    if org is None:
        return

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
                    <contacts_and_albums />
                </panel>
                <panel>
                    <directories />
                </panel>
            </column>
        </row>
    """)


@upgrade_task('Migrate org theme options for foundation6')
def migrate_theme_options(context):
    org = context.session.query(Organisation).first()

    if org is None:
        return

    body_font_family = org.theme_options.get('font-family-sans-serif')
    if body_font_family:
        del org.theme_options['font-family-sans-serif']
        org.theme_options['body-font-family-ui'] = body_font_family
    else:
        org.theme_options['body-font-family-ui'] = MERRIWEATHER

    header_font_family = org.theme_options.get('header-font-family-ui')
    if not header_font_family:
        if body_font_family:
            org.theme_options['header-font-family-ui'] = ROBOTO_CONDENSED

    primary_color = org.theme_options.get('primary-color')
    if primary_color:
        del org.theme_options['primary-color']
        org.theme_options['primary-color-ui'] = primary_color


@upgrade_task('Add structure for foundation layout')
def migrate_homepage_structure(context):
    org = context.session.query(Organisation).first()

    if org is None:
        return

    if '<services />' not in org.meta['homepage_structure']:
        return

    org.meta['homepage_structure'] = textwrap.dedent("""\
        <row-wide>
            <column span="12">
                <slider />
            </column>
        </row-wide>
        <row>
            <column span="12">
                <row>
                    <column span="8">
                    </column>
                    <column span="4">
                        <panel>
                            <services />
                        </panel>
                    </column>
                </row>
                <line />
            </column>
        </row>
        <row>
            <column span="12">
                <news />
            </column>
        </row>
        <line />
        <row>
            <column span="12">
                <events />
            </column>
        </row>
        <line />
        <row>
            <column span="12">
                <homepage-tiles />
            </column>
        </row>
        <line />
        <row>
            <column span="12">
                <directories />
            </column>
        </row>
        <row>
            <column span="12">
                <partners />
            </column>
        </row>
    """)
