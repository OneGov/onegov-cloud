""" Contains upgrade tasks that are executed when the application is being
upgraded on the server. See :class:`onegov.core.upgrade.upgrade_task`.

"""
# pragma: exclude file
from __future__ import annotations

import textwrap

from onegov.town6.theme.town_theme import MERRIWEATHER, ROBOTO_CONDENSED
from onegov.core.upgrade import upgrade_task, UpgradeContext
from onegov.org.models import Organisation


@upgrade_task('Migrate org theme options for foundation6')
def migrate_theme_options(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org is None:
        return

    assert org.theme_options is not None
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
def migrate_homepage_structure_for_town6(context: UpgradeContext) -> None:
    org = context.session.query(Organisation).first()

    if org is None:
        return

    if '<services />' not in org.meta['homepage_structure']:
        return

    org.meta['homepage_structure'] = textwrap.dedent("""\
<slider />
<row>
    <column span="8">
        <focus />
    </column>
    <column span="4">
        <panel>
            <services />
        </panel>
    </column>
</row>
<row-wide bgcolor="gray">
    <column span="12">
        <row>
            <column span="12">
                <news />
            </column>
        </row>
    </column>
</row-wide>
<row-wide bgcolor="primary">
    <column span="12">
        <row>
            <column span="12">
                <events />
            </column>
        </row>
    </column>
</row-wide>
<row>
    <column span="12">
        <homepage-tiles show-title="True"/>
    </column>
</row>
<row>
    <column span="12">
        <directories />
    </column>
</row>
<row-wide bgcolor="gray">
    <column span="12">
        <row>
            <column span="12">
                <partners />
            </column>
        </row>
    </column>
</row-wide>
    """)
