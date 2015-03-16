from onegov.foundation import BaseTheme, Theme


def test_compile():
    # see if the base theme actually compiles

    theme = Theme(compress=False)
    assert theme.compile() == theme.compile()
    assert theme.compile() != Theme(compress=True).compile()


def test_options():
    # override a simple variable provided by zurb foundation

    theme = Theme(compress=False)

    assert '#a0d3e8' in theme.compile()
    assert '#a0d3e8' not in theme.compile({'info-color': '#aa33aa'})

    class MyTheme(BaseTheme):

        default_options = {
            'info-color': '#aa33aa'
        }

    theme = MyTheme(compress=False)
    assert '#aa33aa' in theme.compile()
    assert '#a0d3e8' not in theme.compile()
    assert '#aa00bb' in theme.compile({'info-color': '#aa00bb'})
    assert '#aa33aa' not in theme.compile({'info-color': '#aa00bb'})
