from onegov.people.cli import parse_and_split_address_field, \
    parse_agency_portrait_field_for_address


def test_parse_person_address_field():
    test_cases = [
        # address, expected result after splitting
        ('', ('', '', '', '')),
        ('Leimenstrasse 1, 4001 Basel',
         ('', '', 'Leimenstrasse 1', '4001 Basel')),
        ('Pilatusstrasse 3\n6003 Luzern',
         ('', '', 'Pilatusstrasse 3', '6003 Luzern')),
        ('Bauverwaltung Lauerz\nHusmatt 1\n6424 Lauerz',
         ('', '', 'Bauverwaltung Lauerz\nHusmatt 1', '6424 Lauerz')),
        ('Meier AG\nBüro für Softis\nMit viel Spass bei der Arbeit\nPostfach '
         '41\n1234 Govikon',
         ('', '', 'Meier AG\nBüro für Softis\nMit viel Spass bei der '
                  'Arbeit\nPostfach 41', '1234 Govikon')),
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
         'Rittergasse 4, 4001 Basel',
         ('Sekretariat, Hörnliallee 70', '4125 Riehen', 'Rittergasse 4',
          '4001 Basel')),
        ('Eichmatt 47', ('', '', 'Eichmatt 47', '')),
        ('An der Aa 4a', ('', '', 'An der Aa 4a', '')),
        ('Grundhof', ('', '', 'Grundhof', '')),
    ]

    for address, expected in test_cases:
        result = parse_and_split_address_field(address)
        assert result == expected


def test_parse_agency_portrait_field_for_address():
    test_cases = [
        # portrait in html, expected result after splitting
        ('<p><a href="www.bgbasel.ch">Homepage</a><br></p>',
         ('', '', '', '')),
        ('<p>c/o Bürgergemeinde der Stadt Basel<br><br>Tel.: <a '
         'href="tel:+41 61 269 96 10">+41 61 269 96 10</a><br></p>',
            ('', '', '', '')),
        ('<p><a href="http://www.grosserrat.bs.ch/de/mitglieder-gremien'
         '/kommissionen-und-weitere-gremien/weitere-kommissionen">Homepage'
         '</a><br></p>',
            ('', '', '', '')),
        ('<p>Stadthausgasse 13<br>4001 Basel<br><br>Tel.: <a href="tel:+41 '
         '61 269 96 10">+41 61 269 96 10</a><br>Fax: <a href="tel:+41 61 269 '
         '96 30">+41 61 269 96 30</a><br><a '
         'href="mailto:stadthaus@bgbasel.ch">stadthaus@bgbasel.ch</a><br><a '
         'href="www.bgbasel.ch">Homepage</a><br></p>',
            ('', '', 'Stadthausgasse 13', '4001 Basel')),
        ('<p>Theodorskirchplatz 7<br>4058 Basel<br><br>Tel.: <a '
         'href="tel:+41 61 699 33 11">+41 61 699 33 11</a><br>Fax: <a '
         'href="tel:+41 61 699 33 00">+41 61 699 33 00</a><br><a '
         'href="www.waisenhaus-basel.ch">Homepage</a><br></p>',
            ('', '', 'Theodorskirchplatz 7', '4058 Basel')),
        ('<p>Wettsteinstrasse 1<br>4125 Riehen<br><br>Postfach<br>4125 '
         'Riehen 1<br><br>Tel.: <a href="tel:+41 61 646 81 11">+41 61 646 81 '
         '11</a><br>Fax: <a href="tel:+41 61 646 81 41">+41 61 646 81 '
         '41</a><br><a href="http://www.riehen.ch">Homepage</a><br></p>',
            ('Wettsteinstrasse 1', '4125 Riehen', 'Postfach',
             '4125 Riehen 1')),
        ('<p>De Wette-Strasse 3<br>4051 Basel<br><br>De Wette-Strasse '
         '3<br>Postfach<br>4010 Basel<br><br>Tel.: <a href="tel:+41 61 267 '
         '48 70">+41 61 267 48 70</a><br><a '
         'href="mailto:ffdf@bs.ch">ffdf@bs.ch</a><br><a '
         'href="http://www.jfs.bs.ch/deutschfoerderung">Homepage</a><br></p>',
            ('De Wette-Strasse 3', '4051 Basel',
             'De Wette-Strasse 3\nPostfach', '4010 Basel')),
        ('<p>Rebgasse 1<br>Postfach<br>4005 Basel<br><br>Tel.: <a '
         'href="tel:+41 61 685 90 20">+41 61 685 90 20</a><br>Fax: <a '
         'href="tel:+41 61 685 90 29">+41 61 685 90 29</a><br><a '
         'href="mailto:sekretariat@sp-bs.ch">sekretariat@sp-bs.ch</a><br><a '
         'href="http://www.sp-bs.ch/">Homepage</a><br></p>',
            ('', '', 'Rebgasse 1\nPostfach', '4005 Basel')),
        ('<p>Postfach 1220<br>D-79574 Weil am Rhein<br><br>Tel.: +49 7621 '
         '704-0<br>Fax: +40 7621 704-123<br><a '
         'href="mailto:stadt@weil-am-rhein.de">stadt@weil-am-rhein.de</a><br'
         '><a href="http://www.weil-am-rhein.de/">Homepage</a><br></p>',
            ('', '', 'Postfach 1220', 'D-79574 Weil am Rhein')),
        ('<p>Haus der Kantone<br>Postfach 444<br>3000 Bern 7<br><br></p>',
         ('', '', 'Haus der Kantone\nPostfach 444', '3000 Bern 7')),
        ('<p>3862 Innertkirchen<br><br>Homepage</p>',
         ('', '', '', '3862 Innertkirchen')),
        ('<p>c/o Dr. Guido Stebler<br>Grundackerstrasse 14d<br>4414 '
         'Füllinsdorf<br><br>Tel.: <a href="tel:+41 61 902 19 68">+41 61 902 '
         '19 68</a><br><a href="mailto:g.stebler@bluewin.ch">g.stebler'
         '@bluewin.ch</a><br></p>',
            ('', '', 'Grundackerstrasse 14d', '4414 Füllinsdorf')),
    ]

    for portrait, expected in test_cases:
        result = parse_agency_portrait_field_for_address(portrait)
        assert result == expected
