from onegov.core.utils import scan_morepath_modules
from onegov.town6 import TownApp
from onegov.org.homepage_widgets.core import transform_homepage_structure


def test_focus_widget():

    class App(TownApp):
        pass

    scan_morepath_modules(App)
    App.commit()

    result = transform_homepage_structure(App(), """
        <focus hide-lead="yep" hide-text="of course"/>
    """)
    assert 'hide_lead True;' in result
    assert 'hide_text True;' in result

    result = transform_homepage_structure(App(), """
            <focus title="My Fokus"/>
        """)

    assert '<h3>My Fokus</h3>' in result

    result = transform_homepage_structure(App(), """
                <focus title="My Fokus" hide-title="any value" />
            """)
    assert 'My Fokus' not in result

    result = transform_homepage_structure(App(), """
                    <focus image-src="#" image-url="###"/>
                """)
    assert "image_src '#';" in result
    assert "image_url '###';" in result

    result = transform_homepage_structure(App(), """
                       <focus page-path="kontakt/gemeinde" hide-title="yes" />
                   """)

    defined = " ".join((
        'page_path',
        "'kontakt/gemeinde';",
        'hide_title', 'True;',
        'hide_lead', 'False;',
        'hide_text', 'False;',
        'image_src', 'None;',
        'image_url', 'None;',
    ))
    assert f'tal:define="{defined}"' in result
