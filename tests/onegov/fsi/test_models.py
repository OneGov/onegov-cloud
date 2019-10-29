def test_course(course):
    course, data = course
    for key, val in data.items():
        assert getattr(course, key) == val
