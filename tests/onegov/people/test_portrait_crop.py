import numpy as np

from onegov.people.portrait_crop import (
    is_quadratic,
    find_biggest_rectangle,
)


def test_is_quadratic():
    quadratic_rectangles = np.array(
        [[0, 0, 1, 1], [0, 0, 2, 2], [10, 10, 20, 20]]
    )
    for rectangle in quadratic_rectangles:
        assert is_quadratic(rectangle)


def test_find_biggest_rectangle():
    some_rectangles = np.array(
        [[0, 0, 1, 1], [0, 0, 2, 2], [0, 0, 3, 3], [0, 0, 4, 4]]
    )
    max_rect = find_biggest_rectangle(some_rectangles)
    assert np.array_equal(max_rect, np.array([0, 0, 4, 4]))

    some_rectangles = np.array([[100, 100, 500, 500], [0, 0, 200, 200]])

    max_rect = find_biggest_rectangle(some_rectangles)
    assert np.array_equal(max_rect, np.array([100, 100, 500, 500]))
