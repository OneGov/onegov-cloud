from onegov.core.utils import scan_morepath_modules
from onegov.core.widgets import transform_structure
from onegov.town6 import TownApp


def test_focus_widget():

    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    widgets = App().config.homepage_widget_registry.values()
    result = transform_structure(widgets, """
        <focus hide-lead="yep" hide-text="of course"/>
    """)
    assert 'hide_lead True;' in result
    assert 'hide_text True;' in result

    result = transform_structure(widgets, """
        <focus title="My Fokus"/>
    """)

    assert '<h3>My Fokus</h3>' in result

    result = transform_structure(widgets, """
        <focus title="My Fokus" hide-title="any value" />
    """)
    assert 'My Fokus' not in result

    result = transform_structure(widgets, """
        <focus image-src="#" image-url="###"/>
    """)
    assert "image_src '#';" in result
    assert "image_url '###';" in result


def test_partner_widget():
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


def test_services_widget(town_app):
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


def test_text_widgets(town_app):
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


def test_video_widget(town_app):
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
