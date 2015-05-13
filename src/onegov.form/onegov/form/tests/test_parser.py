from onegov.form.parser import parse


def test_parse_complete_form():
    # a form that includes all the features available
    form = """
        First name* = ___
        Last name* = ___
        E-Mail* = /E-Mail
        Country = {(CH > Switzerland), DE, FR > France}

        # Order
        Parts = [] Screen [x] Keyboard [] Mouse
        Assembly = (x) Assembly ( ) I want to do my own assembly

        #

        Comment = ...[30*4]

        [Submit]
    """

    collections = list(parse(form))

    len(collections) == 3

    assert not collections[0].label
    assert len(collections[0]) == 4

    assert collections[0][0].label == 'First name'
    assert collections[0][0].required
    assert collections[0][0].field.type == 'text'
    assert collections[0][0].required

    assert collections[0][1].label == 'Last name'
    assert collections[0][1].required
    assert collections[0][1].field.type == 'text'

    assert collections[0][2].label == 'E-Mail'
    assert collections[0][2].required
    assert collections[0][2].field.type == 'custom'
    assert collections[0][2].field.custom_id == 'e-mail'

    assert collections[0][3].label == 'Country'
    assert not collections[0][3].required
    assert collections[0][3].field.type == 'select'
    assert collections[0][3].field[0].key == 'CH'
    assert collections[0][3].field[0].label == 'Switzerland'
    assert collections[0][3].field[1].key == ''
    assert collections[0][3].field[1].label == 'DE'
    assert collections[0][3].field[2].key == 'FR'
    assert collections[0][3].field[2].label == 'France'

    assert collections[1].label == 'Order'
    assert len(collections[1]) == 2

    assert collections[1][0].field.type == 'checkbox'
    assert collections[1][0].field[0].label == 'Screen'
    assert not collections[1][0].field[0].checked
    assert collections[1][0].field[1].label == 'Keyboard'
    assert collections[1][0].field[1].checked
    assert collections[1][0].field[2].label == 'Mouse'
    assert not collections[1][0].field[2].checked

    assert collections[1][1].field.type == 'radio'
    assert collections[1][1].field[0].label == 'Assembly'
    assert collections[1][1].field[0].checked
    assert collections[1][1].field[1].label == 'I want to do my own assembly'
    assert not collections[1][1].field[1].checked

    assert not collections[2].label
    assert len(collections[2]) == 2

    assert collections[2][0].label == 'Comment'
    assert collections[2][0].field.type == 'textarea'
    assert collections[2][0].field.cols == 30
    assert collections[2][0].field.rows == 4

    assert collections[2][1].type == 'button'
    assert collections[2][1].label == 'Submit'
