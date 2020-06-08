def test_audit_for_course(client, scenario):
    admin = client.login_admin()
    assert scenario.session == client.app.session()
    course = scenario.add_course()
    scenario.commit()
    page = client.get(f'/fsi/audit?course_id={course.id}')
