def test_allowed_application_id(org_app):
    # little bobby tables!
    assert not org_app.is_allowed_application_id(
        "Robert'); DROP TABLE Students; --"
    )
    assert not org_app.is_allowed_application_id('foo')
    org_app.session_manager.ensure_schema_exists(org_app.namespace + '-foo')
    assert org_app.is_allowed_application_id('foo')
