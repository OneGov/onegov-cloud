from onegov.core import filters  # noqa -> registers webasset filters


def test_integration(app, endpoint_class):
    assert app.rate_limit == (100, 900)
