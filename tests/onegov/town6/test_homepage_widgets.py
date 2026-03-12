from __future__ import annotations

from onegov.core.utils import scan_morepath_modules
from onegov.core.widgets import transform_structure
from onegov.town6 import TownApp
from onegov.town6.homepage_widgets import parsed_rss
from datetime import datetime, timezone, timedelta


def test_focus_widget() -> None:

    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()
    result = transform_structure(widgets, """
        <focus title="My Fokus"/>
    """)

    assert '<h5>My Fokus</h5>' in result

    result = transform_structure(widgets, """
        <focus image-src="#"/>
    """)
    assert "image_src '#';" in result


def test_partner_widget() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()
    result = transform_structure(widgets, """
        <partners />
    """)
    assert 'tal:define="title \'\'; show_title True;"' in result

    result = transform_structure(widgets, """
        <partners title="TEST" />
    """)
    assert 'tal:define="title \'TEST\'; show_title True;"' in result

    result = transform_structure(widgets, """
            <partners hide-title="True" />
        """)
    assert 'tal:define="title \'\'; show_title False;"' in result


def test_services_widget() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()
    structure = """
        <services>
            <link url="#">XYZ</link>
            <link icon="address-book" url="#">XYZ</link>
        </services>
    """
    result = transform_structure(widgets, structure)
    assert 'link services_panel.links' in result
    assert 'tal:define="icon \'\'' in result
    assert 'tal:define="icon \'address-book\'' in result


def test_text_widgets() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()
    structure = """
            <title>A h3 title</title>
            <text>Normal text</text>

    """
    result = transform_structure(widgets, structure)
    assert '<h3 class="">A h3 title</h3>' in result
    assert '<p class="homepage-text">Normal text</p>' in result


def test_video_widget() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()

    structure = "<autoplay_video link_mp4='/video.mp4' max-height='40vh'/>"

    result = transform_structure(widgets, structure)
    assert 'use-macro="layout.macros.autoplay_video"' in result
    assert "link_mp4 \'/video.mp4\'" in result
    assert "max_height \'40vh\'" in result
    assert "link_webm \'\'" in result


def test_link_icon_widget() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()

    structure = "<icon_link title='Services'/>"
    result = transform_structure(widgets, structure)
    assert 'use-macro="layout.macros.icon_link"' in result
    assert 'icon-link' not in result

    structure = """
        <icon_link title='Services' icon='fa-user'
        link='https://www.test.ch' text='Whenever you want'
        />
    """
    result = transform_structure(widgets, structure)
    assert "icon \'fa-user\'" in result
    assert "link \'https://www.test.ch\'" in result
    assert "text \'Whenever you want\'" in result


def test_testimonial_widget() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()

    structure = """
        <testimonial image='/files/image.jpg' description='Doctor'
        quote='very good hospital'
    />
    """

    result = transform_structure(widgets, structure)
    assert 'use-macro="layout.macros.testimonial"' in result
    assert "image \'/files/image.jpg\'" in result
    assert "description \'Doctor\'" in result
    assert "quote \'very good hospital\'" in result


def test_testimonial_slider_widget() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()

    structure = """
        <testimonial_slider image_1='/files/image.jpg' description_1='Doctor'
        quote_1='very good hospital' image_2='/files/image_2.jpg'
        description_2='Nurse' quote_2='so much space'
    />
    """

    result = transform_structure(widgets, structure)
    assert 'use-macro="layout.macros.testimonial_slider"' in result
    assert "image_1 \'/files/image.jpg\'" in result
    assert "description_1 \'Doctor\'" in result
    assert "quote_1 \'very good hospital\'" in result
    assert "image_2 \'/files/image_2.jpg\'" in result
    assert "description_2 \'Nurse\'" in result
    assert "quote_2 \'so much space\'" in result


def test_parse_rss_to_named_tuple() -> None:
    rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title><![CDATA[example.com RSS feed]]></title>
            <link><![CDATA[https://www.example.com]]></link>
            <description><![CDATA[Die Suchresultate für deine Jobsuche]]>
            </description>
            <language><![CDATA[de]]></language>
            <copyright><![CDATA[Copyright (C) 2023 AG]]></copyright>
            <item>
                <title><![CDATA[Sachbearbeiter/-in]]></title>
                <description><![CDATA[Gemeinde Govikon]]></description>
                <guid><![CDATA[https://www.example.com/jobs/~job77736]]></guid>
                <pubDate><![CDATA[Thu, 07 Sep 2023 00:00:00 +0200]]></pubDate>
            </item>
            <item>
                <title><![CDATA[Fachperson Bauberatung 60-100%]]></title>
                <description><![CDATA[Gemeinde Govikon]]></description>
                <guid><![CDATA[https://www.example.com/jobs/~job76358]]></guid>
                <pubDate><![CDATA[Mon, 21 Aug 2023 00:00:00 +0200]]></pubDate>
            </item>
        </channel>
    </rss>
    """.encode('utf-8')

    parsed_channel = parsed_rss(rss)

    assert parsed_channel.title == "example.com RSS feed"
    assert parsed_channel.link == "https://www.example.com"
    assert (
        parsed_channel.description.strip()
        == "Die Suchresultate für deine Jobsuche"
    )
    assert parsed_channel.language == "de"
    assert parsed_channel.copyright == "Copyright (C) 2023 AG"
    sd = list(parsed_channel.items)

    first_item = sd[0]
    assert first_item.title == "Sachbearbeiter/-in"
    assert first_item.description == "Gemeinde Govikon"
    assert first_item.guid == "https://www.example.com/jobs/~job77736"

    assert first_item.pubDate == datetime(
        2023, 9, 7, 0, 0,
        tzinfo=timezone(timedelta(seconds=7200)),
    )

    second_item = sd[1]
    assert second_item.title == "Fachperson Bauberatung 60-100%"
    assert second_item.description == "Gemeinde Govikon"
    assert second_item.guid == "https://www.example.com/jobs/~job76358"

    assert second_item.pubDate == datetime(
        2023, 8, 21, 0, 0,
        tzinfo=timezone(timedelta(seconds=7200)),
    )


def test_rss_jobs_widget() -> None:
    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()

    structure = """<jobs
                rss_feed="example.com"
                jobs_card_title="wir suchen" >
            </jobs>
            """
    result = transform_structure(widgets, structure)

    assert "wir suchen" in result
