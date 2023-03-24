from onegov.people.upgrade import parse_and_split_address_field


def test_parse_person_address_field_2():
    test_cases = [
        # address, expected result after splitting
        ('', ('', '', '', '')),
        ('Leimenstrasse 1, 4001 Basel',
         ('', '', 'Leimenstrasse 1', '4001 Basel')),
        ('Strassburgerallee 12-18, 4055 Basel',
         ('', '', 'Strassburgerallee ' '12-18', '4055 Basel')),
        ('St. Alban-Graben 5, 4010 Basel',
         ('', '', 'St. Alban-Graben 5', '4010 Basel')),
        ('Unterbrüglingen 31, 4142 MünchensteinPostadresse: Postfach, '
         '4001 Basel',
         ('Unterbrüglingen 31', '4142 Münchenstein', 'Postfach',
          '4001 Basel')),
        ('Wallstrasse 22, BaselPostadresse: Münsterplatz 11, 4001 Basel',
         ('Wallstrasse 22', 'Basel', 'Münsterplatz 11', '4001 Basel')),
        ('Hörnliallee70, 4125 RiehenPostadresse: Postfach, 4001 Basel',
         ('Hörnliallee70', '4125 Riehen', 'Postfach', '4001 Basel')),
        ('Fischmarkt 10, Postfach, 4001 Basel',
         ('', '', 'Fischmarkt 10\nPostfach', '4001 Basel')),
        ('Spiegelhof, Spiegelgasse 6, 4001 Basel',
         ('', '', 'Spiegelhof\nSpiegelgasse 6', '4001 Basel')),
        ('Sekretariat, Hörnliallee 70, 4125 Riehen; Postadresse: '
         'Rittergasse 4, ' '' '4001 Basel',
         ('Sekretariat, Hörnliallee 70', '4125 Riehen',
          'Rittergasse 4', '4001 Basel')),
        ('Eichmatt 47', ('', '', 'Eichmatt 47', '')),
        ('An der Aa 4a', ('', '', 'An der Aa 4a', '')),
        ('Grundhof', ('', '', 'Grundhof', '')),
    ]

    for address, expected in test_cases:
        result = parse_and_split_address_field(address)
        assert result == expected
