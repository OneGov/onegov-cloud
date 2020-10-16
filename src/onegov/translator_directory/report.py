from io import BytesIO

from xlsxwriter import Workbook

from onegov.translator_directory.layout import DefaultLayout

"""
https://xlsxwriter.readthedocs.io/working_with_formulas.html

Write in the xlsx format

"""


class TranslatorVoucher(object):

    title = 'Abrechungsbeleg Übersetzende'
    title_font_size = 12
    font_size = 10
    subheader_font_size = 10
    footer_font_size = 8
    default_row_height = 12.7     # 4.5mm
    edit_color = 'ffffcc'
    blue = '0066cc'
    green = '008000'
    light_green = '00ff00'
    white = 'ffffff'
    lila = 'ccccff'

    default_fmt = {
        'font_name': 'Arial',
        'locked': True,
        'font_size': font_size,
        'valign': 'vcenter'
    }

    def __init__(self, request, translator):
        self.request = request
        self.translator = translator
        self.file = BytesIO()
        self.wb = Workbook(self.file)
        self.ws = self.wb.add_worksheet()
        self.layout = DefaultLayout(translator, request)

        # Formats
        input_centered = {
            'bg_color': self.edit_color, 'align': 'center', 'locked': False}
        centered = {'align': 'center'}
        border_blue = {'border': 1, 'border_color': self.blue}
        border_green = {'border': 1, 'border_color': self.green}
        right_green = {'right': 1, 'right_color': self.green}
        left_green = {'left': 1, 'left_color': self.green}
        bottom_green = {'bottom': 1, 'bottom_color': self.green}
        right_blue = {'right': 1, 'right_color': self.blue}
        left_blue = {'left': 1, 'left_color': self.blue}
        bottom_blue = {'bottom': 1, 'bottom_color': self.blue}
        subtotal_default = {'num_format': '#,##0.00', 'italic': True}
        float_default = {'num_format': '0.00', 'align': 'center'}

        self.cell_fmt = self.wb.add_format(self.default_fmt)
        self.cell_fmt_green_last = self.wb.add_format({
            **self.default_fmt, **bottom_green
        })

        self.cell_fmt_blue_last = self.wb.add_format({
            **self.default_fmt, **bottom_blue
        })

        self.title_fmt = self.add_format({
            'font_size': self.title_font_size, 'bold': True
        })
        total_fmt = {
            'bold': True,
            'font_size': self.title_font_size - 1,
            'font_color': self.white,
            'bg_color': self.blue
        }
        self.total_fmt = self.add_format(total_fmt)
        self.total_fmt_float = self.add_format({**total_fmt, **float_default})

        self.editable_fmt = self.add_format({
            'bg_color': self.edit_color, 'locked': False
        })

        self.thead_blue = self.add_format({
            'bold': True,
            'font_size': self.subheader_font_size,
            'font_color': self.white,
            'bg_color': self.blue,
            **border_blue
        })
        self.thead_green = self.add_format({
            'bold': True,
            'font_size': self.subheader_font_size,
            'font_color': self.white,
            'bg_color': self.green,
            **border_green
        })

        self.thead_lightgreen = self.add_format({
            'font_size': self.subheader_font_size,
            'bg_color': self.light_green,
            **centered
        })

        self.thead_lightgreen_green_first = self.add_format({
            'font_size': self.subheader_font_size,
            'bg_color': self.light_green,
            **centered,
            **left_green
        })
        self.thead_lightgreen_green_last = self.add_format({
            'font_size': self.subheader_font_size,
            'bg_color': self.light_green,
            'right': 1,
            'right_color': self.green,
            **centered,
            **right_green
        })

        self.thead_lila = self.add_format({
            'bg_color': self.lila,
            'font_size': self.subheader_font_size,
            **centered,
        })

        self.thead_lila_blue_first = self.add_format(
            {'bg_color': self.lila, **left_blue})

        self.thead_lila_blue_last = self.add_format({
            'bg_color': self.lila, **centered, **right_blue
        })

        self.input_dt_fmt = self.add_format(
            {'num_format': 'H:MM', **input_centered}
        )
        self.input_dt_fmt_green_last = self.add_format(
            {'num_format': 'H:MM', **input_centered, **bottom_green}
        )
        self.input_dt_fmt_blue_last = self.add_format(
            {'num_format': 'H:MM', **input_centered, **bottom_blue}
        )
        self.input_float_fmt = self.add_format(
            {'num_format': '0.00', **input_centered}
        )
        self.input_float_fmt_blue_last = self.add_format(
            {'num_format': '0.00', **input_centered, **bottom_blue}
        )
        self.input_float_fmt_green_last = self.add_format(
            {'num_format': '0.00', **input_centered, **bottom_green}
        )
        self.input_int_fmt = self.add_format(
            {'num_format': '0', **input_centered}
        )
        self.input_int_fmt_blue_last = self.add_format(
            {'num_format': '0', **input_centered, **bottom_blue}
        )

        self.input_int_fmt_green_last = self.add_format(
            {'num_format': '0', **input_centered, **bottom_green}
        )

        self.input_time_fmt = self.add_format(
            {'num_format': 'HH:MM', **input_centered})

        self.input_time_fmt_blue_last = self.add_format(
            {'num_format': 'HH:MM', **input_centered, **bottom_blue})

        self.input_time_fmt_green_last = self.add_format(
            {'num_format': 'HH:MM', **input_centered, **bottom_green})

        self.time_fmt = self.add_format({
            'num_format': 'HH:MM', **centered
        })

        self.input_date_fmt = self.add_format(
            {'num_format': 'TT.MM.JJJJ', **input_centered})

        self.input_date_fmt_green = self.add_format(
            {'num_format': 'TT.MM.JJJJ', **input_centered, **left_green})

        self.input_date_fmt_green_last = self.add_format({
            'num_format': 'TT.MM.JJJJ',
            **input_centered,
            **left_green,
            **bottom_green
        })

        self.input_date_fmt_blue = self.add_format(
            {'num_format': 'TT.MM.JJJJ', **input_centered, **left_blue})

        self.input_date_fmt_blue_last = self.add_format({
            'num_format': 'TT.MM.JJJJ',
            **input_centered,
            **left_blue,
            **bottom_blue
        })

        self.subtotal_fmt_green = self.add_format({
            **subtotal_default,
            **centered,
            **right_green
        })

        self.subtotal_fmt_green_last = self.add_format({
            **subtotal_default,
            **centered,
            **right_green,
            **bottom_green
        })

        self.subtotal_fmt_blue = self.add_format({
            **subtotal_default,
            **centered,
            **right_blue
        })

        self.subtotal_fmt_blue_last = self.add_format({
            **subtotal_default,
            **centered,
            **right_blue,
            **bottom_blue
        })

        self.float_fmt = self.add_format(float_default)

        self.float_fmt_blue_last = self.add_format(
            {**float_default, **bottom_blue}
        )

        self.float_fmt_green_last = self.add_format(
            {**float_default, **bottom_green}
        )

        self.bg_white_fmt = self.add_format(
            {'bg_color': 'white'}
        )
        self.hour_fmt = self.add_format(
            {'num_format': 'h:mm', **centered}
        )
        self.hour_fmt_green_last = self.add_format(
            {'num_format': 'h:mm', **centered, **bottom_green}
        )
        self.hour_fmt_blue_last = self.add_format(
            {'num_format': 'h:mm', **centered, **bottom_blue}
        )

    def to_width(self, value):
        """Input value or list of values in mm"""
        if isinstance(value, float):
            return value / 2.54
        elif isinstance(value, int):
            return float(value) / 2.54
        elif isinstance(value, list):
            return [val / 2.54 for val in value]

    def protect_with(self, password=None):
        """
        # Default values shown.
            options = {
                'objects':               False,
                'scenarios':             False,
                'format_cells':          False,
                'format_columns':        False,
                'format_rows':           False,
                'insert_columns':        False,
                'insert_rows':           False,
                'insert_hyperlinks':     False,
                'delete_columns':        False,
                'delete_rows':           False,
                'select_locked_cells':   True,
                'sort':                  False,
                'autofilter':            False,
                'pivot_tables':          False,
                'select_unlocked_cells': True,
            }
        """
        options = {'select_locked_cells': False}
        self.ws.protect(password, options)

    def set_col_widths(self, widths, start=0):
        # set the row widths starting from left side
        for col, width in enumerate(widths, start):
            self.ws.set_column(col, col, width)

    def set_page_layout(self):

        def mm_to_inch(mm):
            return mm / 25.4

        self.ws.set_margins(
            left=mm_to_inch(20),
            right=mm_to_inch(10),
            bottom=mm_to_inch(10),
            top=mm_to_inch(17)
        )

        self.ws.set_default_row(self.default_row_height)
        self.ws.set_row(72, 8 * 2.54)
        self.ws.set_paper(9)   # A4
        # center fpr printing
        self.ws.center_horizontally()

        # set print area
        self.ws.print_area('A1:H81')
        self.ws.fit_to_pages(1, 1)  # Fit to 1x1 pages.

        # set col width as mm
        self.set_col_widths(self.to_width([
            21.7, 26.3, 26.3, 22.4, 26, 31.6, 28.5, 38.3
        ]))

    def coerce_fmts(self, raw_formats, use_default=True):
        if len(raw_formats) == 1 and not use_default:
            return raw_formats[0]
        if use_default:
            default_fmt = self.default_fmt.copy()
        else:
            default_fmt = raw_formats.pop(0)

        for fmt in raw_formats:
            default_fmt.update(fmt)
        return default_fmt

    def add_format(self, format, use_default=True):
        return self.wb.add_format(self.coerce_fmts([format], use_default))

    def add_formats(self, formats, use_default=True):
        return self.wb.add_format(self.coerce_fmts(formats, use_default))

    def merge_range(self, position, data, fmt=None):
        return self.ws.merge_range(position, data, fmt or self.default_fmt)

    def write(self, position, data, fmt=None, use_default=True):
        if not fmt and use_default:
            fmt = self.cell_fmt
        self.ws.write(position, data, fmt)

    def set_logo(self):
        """
        worksheet.set_header('&L&G', {'image_left': 'logo.jpg'})
        """
        pass

    def spacer_row(self, rownum, fmt=None):
        return self.ws.set_row(rownum, 1.3 * 2.54, cell_format=fmt)

    def create_header(self):
        self.write('A8', self.title, self.title_fmt)
        amt_fmt = self.add_format({
            'bg_color': self.edit_color, 'locked': False,
            'font_size': 11
        })
        self.merge_range('F8:H8', 'Amt', amt_fmt)

        self.write('A10', 'Einsatzgrund')
        self.write('A11', 'Auftraggebende Person')
        self.write('A12', 'Geschäftskontrolle')

        self.merge_range('C10:E10', None, self.editable_fmt)
        self.merge_range('C11:E11', None, self.editable_fmt)
        self.merge_range('C12:E13', None, self.editable_fmt)

        self.write('F10', 'Übersetzende/r')
        self.write('F11', 'Personalnummer')
        self.write('F12', 'Quellensteuer')
        self.write('F13', 'Übers. Sprache')

        self.write('G10', self.translator.title)
        self.write('G11', str(self.translator.pers_id))
        self.write('G12', self.translator.withholding_tax and 'Ja' or 'Nein')
        self.merge_range('G13:H13', None, self.editable_fmt)

    def fmt(self, key, last=False, first=False, color='blue'):
        """Helper to get formats easier"""
        if last:
            if '_green' in key or '_blue' in key:
                return getattr(self, f'{key}_last')
            return getattr(self, f'{key}_{color}_last')
        elif first:
            if '_green' in key or '_blue' in key:
                return getattr(self, f'{key}_first')
            return getattr(self, f'{key}_{color}_first')
        return getattr(self, key)

    def empty_cell(self, position, color='blue', border_bottom=True):
        self.write(
            position,
            None,
            fmt=self.fmt('cell_fmt', border_bottom, color=color)
        )

    def write_formulas(self):
        fields_for_total = []
        fmt = self.fmt

        def hour_diff(rw):
            return f'=IF(ISBLANK(B{rw}), 0, IF(ISBLANK(C{rw}), 0, ' \
                   f'IF((C{rw}-B{rw})<=0.04,0.04167, C{rw}-B{rw})))'

        for row in range(17, 19 + 1):
            self.ws.write_formula(f'D{row}', hour_diff(row), fmt('hour_fmt'))
            self.ws.write_formula(f'G{row}', f'=D{row}*24', fmt('float_fmt'))
            self.ws.write_formula(
                f'H{row}',
                f'=ROUND((G{row}*75)*2,1)/2',
                fmt('subtotal_fmt_blue')
            )
            fields_for_total.append(f'H{row}')

        for row in range(21, 23 + 1):
            last = row == 23
            self.ws.write_formula(
                f'D{row}',
                hour_diff(row),
                fmt('hour_fmt', last)
            )
            self.ws.write_formula(
                f'G{row}', f'=D{row}*24*1.25', fmt('float_fmt', last))
            self.ws.write_formula(
                f'H{row}',
                f'=ROUND((G{row}*75)*2,1)/2',
                fmt('subtotal_fmt_blue', last)
            )
            for col in ('E', 'F'):
                self.empty_cell(f'{col}{row}', border_bottom=last)

            fields_for_total.append(f'H{row}')

        for row in range(27, 29 + 1):
            self.ws.write_formula(f'D{row}', hour_diff(row), fmt('hour_fmt'))
            self.ws.write_formula(f'G{row}', f'=D{row}*24', fmt('float_fmt'))
            self.ws.write_formula(
                f'H{row}', f'=ROUND((G{row}*95', fmt('subtotal_fmt_blue'))
            fields_for_total.append(f'H{row}')

        for row in range(31, 33 + 1):
            last = row == 33
            self.ws.write_formula(
                f'D{row}', hour_diff(row), fmt('hour_fmt', last))
            self.ws.write_formula(
                f'G{row}', f'=D{row}*24*1.25', fmt('float_fmt', last))
            self.ws.write_formula(
                f'H{row}',
                f'=ROUND((G{row}*95)*2,1)/2',
                fmt('subtotal_fmt_blue', last)
            )
            for col in ('E', 'F'):
                self.empty_cell(f'{col}{row}', border_bottom=last)
            fields_for_total.append(f'H{row}')

        def distance_flatrate_formula(row):
            return f'=IF(B{row}=0,0,IF(B{row}<=20,40,' \
                   f'IF(AND(B{row}>20,B{row}<=40),50,' \
                f'IF(AND(B{row}>40,B{row}<=60),60,' \
                f'IF(AND(B{row}>60,B{row}<=80),70,' \
                f'IF(AND(B{row}>80,B{row}<=100),80,' \
                f'IF(AND(B{row}<100),80,"n. Vereinbarung")))))))'

        for row in range(37, 39 + 1):
            last = row == 39
            self.ws.write_formula(
                f'E{row}',
                distance_flatrate_formula(row),
                fmt('float_fmt', last)
            )
            self.ws.write_formula(
                f'H{row}', f'=E{row}', fmt('subtotal_fmt_blue', last))
            for col in ('D', 'F', 'G'):
                self.empty_cell(f'{col}{row}', border_bottom=last)
            fields_for_total.append(f'H{row}')

        for row in range(43, 45 + 1):
            last = row == 45
            self.ws.write_formula(f'D{row}', f'=C{row}', fmt('hour_fmt', last))
            self.ws.write_formula(
                f'E{row}',
                distance_flatrate_formula(row),
                fmt('float_fmt', last)
            )
            self.ws.write_formula(
                f'G{row}',
                f'=D{row}*24',
                fmt('float_fmt', last)
            )
            self.ws.write_formula(
                f'H{row}',
                f'=ROUND(((F{row}*G{row})+E{row})*2,1)/2',
                fmt('subtotal_fmt_blue', last)
            )
            fields_for_total.append(f'H{row}')

        def round_pages_up(r):
            return f'=IF(ISBLANK(B{r}),0,IF(AND(B{r}<0.5, B{r}>0),0.5,B{r}))'

        for row in range(49, 51 + 1):
            self.ws.write_formula(
                f'D{row}', round_pages_up(row), fmt('float_fmt'))
            self.ws.write_formula(
                f'H{row}',
                f'=ROUND((D{row}*75)*2,1)/2',
                fmt('subtotal_fmt_green')
            )
            fields_for_total.append(f'H{row}')

        for row in range(53, 55 + 1):
            last = row == 55
            self.ws.write_formula(
                f'D{row}', f'=B{row}', fmt('float_fmt', last))
            self.ws.write_formula(f'H{row}', f'=ROUND((D{row}*75*1.25)*2,1)/2',
                                  fmt('subtotal_fmt_green', last))
            for col in ('C', 'E', 'F', 'G'):
                self.empty_cell(f'{col}{row}', 'green', border_bottom=last)
            fields_for_total.append(f'H{row}')

        for row in range(59, 61 + 1):
            self.ws.write_formula(f'D{row}', f'=B{row}', fmt('float_fmt'))
            self.ws.write_formula(f'H{row}', f'=ROUND((D{row}*95*1.25)*2,1)/2',
                                  fmt('subtotal_fmt_green'))
            fields_for_total.append(f'H{row}')

        for row in range(63, 65 + 1):
            last = row == 65
            self.ws.write_formula(
                f'D{row}', f'=B{row}', fmt('float_fmt', last))
            self.ws.write_formula(f'H{row}', f'=ROUND((D{row}*95*1.25)*2,1)/2',
                                  fmt('subtotal_fmt_green', last))
            for col in ('C', 'E', 'F', 'G'):
                self.empty_cell(f'{col}{row}', 'green', border_bottom=last)
            fields_for_total.append(f'H{row}')

        for row in range(69, 71 + 1):
            last = row == 71
            self.ws.write_formula(
                f'D{row}', hour_diff(row), fmt('float_fmt', last))
            self.ws.write_formula(
                f'G{row}', f'=D{row}*24', fmt('float_fmt', last))
            self.ws.write_formula(f'H{row}', f'=ROUND((G{row}*E{row})*2,1)/2',
                                  fmt('subtotal_fmt_blue', last))
            self.empty_cell(f'F{row}', border_bottom=last)
            fields_for_total.append(f'H{row}')

        self.ws.write(
            'H73',
            f'=ROUND(({"+".join(fields_for_total)})*2,1)/2',
            self.total_fmt_float
        )

    def create_table(self, row):
        fmt = self.fmt
        subtitles = (
            'Datum', 'von', 'bis', 'Total', '', '', 'Industrieminuten',
            'Zwischentotal'
        )
        col_span = len(subtitles)
        subheader_fmts = (col_span + 1) * ('thead_lila', )

        def headers(row, text, format_=None):
            if not format_:
                format_ = self.thead_blue
            self.merge_range(f'A{row+1}:H{row+1}', text, format_)

        def subheaders(row, subtitles, fmt, border_color='blue'):
            for col_ix, (text, fmt_) in enumerate(zip(subtitles, fmt)):
                first = col_ix == 0
                last = col_ix == len(subtitles) - 1
                format_ = self.fmt(fmt_, last, first, border_color)
                self.ws.write(row, col_ix, text, format_)

        def input_block(
                start_row,
                start_col,
                numrows,
                formats,
                border_bottom=False,
                color='blue'
        ):
            for ix in range(numrows):
                for yx, format in enumerate(formats):
                    last = border_bottom and ix == numrows - 1
                    self.ws.write(
                        start_row + ix,
                        start_col + yx,
                        None,
                        fmt(format, last=last, color=color)
                    )

        headers(row, 'Dolmetschertätigkeit - '
                     '(§ 15 Abs. 1 lit. a, 06:00-20:00 Uhr)')
        subheaders(row + 1, subtitles, subheader_fmts)
        date_time_fmts = [
            'input_date_fmt_blue', 'input_time_fmt', 'input_time_fmt']

        input_block(row + 2, 0, numrows=3, formats=date_time_fmts)

        headers(row + 5, 'Dolmetschertätigkeit - zuschlagsberechtigter '
                         'Zeitraum +25 %   '
                         '- (§ 15 Abs. 1 lit. b, 20:00-06:00)')
        input_block(
            row + 6, 0, numrows=3, formats=date_time_fmts, border_bottom=True)
        self.spacer_row(row + 9)

        headers(row + 10, 'Dolmetschertätigkeit bei ausserordentlich '
                          'schwierigen Übersetzungen  - '
                          '(§ 15 Abs. 1 lit. c, 06:00-20:00 Uhr)')

        subheaders(row + 11, subtitles, subheader_fmts)
        input_block(row + 12, 0, numrows=3, formats=date_time_fmts)

        headers(row + 15, 'Bei ausserordentlich '
                          'schwierigen Übersetzungen - '
                          'zuschlagsberechtigter Zeitraum +25 % - '
                          '(§ 15 Abs. 1 lit. b, 20:00-06:00)')
        input_block(
            row + 16, 0, numrows=3, formats=date_time_fmts, border_bottom=True)
        self.spacer_row(row + 19)
        headers(row + 20, 'Wegpauschale - (§ 15 Abs. 1 lit.g)')

        subheaders(row + 21, (
            'Datum', 'Reiseweg in km', '', '', 'Wegpauschale', '', '',
            'Zwischentotal'), subheader_fmts)
        input_fmts = ['input_date_fmt_blue', 'input_int_fmt', 'input_dt_fmt']

        input_block(
            row + 22, 0, numrows=3, formats=input_fmts, border_bottom=True)
        self.spacer_row(row + 25)

        headers(row + 26, 'Besondere Dringlichkeit - (§ 15 Abs. 1 lit. f - '
                          'Wegpauschale+Reisezeit - Std.- Ansatz CHF 75.00)')
        subheaders(row + 27, ('Datum', 'Reiseweg in km', 'Reisezeit',
                                 'Total', 'Wegpauschale', '1/2 Ansatz',
                                 'Industrieminuten', 'Zwischentotal'),
                   subheader_fmts
                   )
        input_block(
            row + 28, 0, numrows=3, formats=input_fmts, border_bottom=True)
        self.ws.write_number(row + 28, 5, 37.50, fmt('float_fmt'))
        self.ws.write_number(row + 29, 5, 37.50, fmt('float_fmt'))
        self.ws.write_number(row + 30, 5, 37.50, fmt('float_fmt', last=True))
        self.spacer_row(row + 31)

        # Begin of green table
        headers(
            row + 32,
            'Übersetzungstätigkeit - (§ 15 Abs. 2 lit. a)',
            self.thead_green
        )
        subtitles = ('Datum', 'Anzahl Seiten', '', 'Total', '', '', '',
                     'Zwischentotal')
        subheader_fmts = (col_span + 1) * ('thead_lightgreen',)

        input_fmts = ['input_date_fmt_green', 'input_float_fmt']
        subheaders(
            row + 33, subtitles, fmt=subheader_fmts, border_color='green')
        input_block(row + 34, 0, numrows=3, formats=input_fmts)

        headers(
            row + 37,
            'Übersetzungstätigkeit - zuschlagsberechtigter Zeitraum +25 % - '
            '(§ 15 Abs. 2 lit. c)',
            self.thead_green
        )
        input_fmts = ['input_date_fmt_green', 'input_int_fmt']
        input_block(
            row + 38,
            0,
            numrows=3,
            formats=input_fmts,
            border_bottom=True,
            color='green'
        )
        self.spacer_row(row + 41)
        headers(row+42, 'Übersetzungstätigkeit bei ausserordentlich '
                        'schwierigen Übersetzungen - (§ 15 Abs. 2 lit. b)',
                self.thead_green)
        subheaders(
            row + 43, subtitles, fmt=subheader_fmts, border_color='green')
        input_block(row + 44, 0, numrows=3, formats=input_fmts)
        headers(
            row + 47,
            'Übersetzungstätigkeit bei ausserordentlich schwierigen '
            'Übersetzungen - zuschlagsberechtigter Zeitraum +25 % - '
            '(§ 15 Abs. 2 lit. c)',
            self.thead_green
        )
        input_block(
            row + 48,
            0,
            numrows=3,
            formats=input_fmts,
            border_bottom=True,
            color='green'
        )
        self.spacer_row(row + 51)
        headers(row + 52, 'Einsätze nach Vereinbarung (§ 15 Abs. 1 lit. d '
                        'oder e / § 15 Abs. 2 lit. d)'
                )
        subheader_fmts = (col_span + 1) * ('thead_lila',)

        subheaders(row + 53, (
            'Datum', 'von', 'bis', 'Total', 'Vereinb. Ansatz', '',
            'Industrieminuten', 'Zwischentotal'), subheader_fmts)

        input_block(
            row + 54,
            0, numrows=3,
            formats=(
            'input_date_fmt_blue', 'input_time_fmt', 'input_time_fmt'),
            border_bottom=True
        )
        input_block(
            row + 54,
            4,
            numrows=3,
            formats=['input_float_fmt'],
            border_bottom=True
        )
        self.spacer_row(row + 57)

        # Main Total
        self.merge_range(
            f'A{row + 59}:G{row + 59}', 'Gesamttotal', self.total_fmt)

    def create_footer(self):
        colspan = 7
        default = {
            'bg_color': self.white,
            'font_size': self.footer_font_size,
            'align': 'left'
        }
        input_ = {
            'num_format': 'TT.MM.JJJJ',
            'locked': False,
            'bg_color': self.edit_color,
            'align': 'center',
            'font_size': self.footer_font_size
        }
        bottom = {'bottom': 1, 'bottom_color': self.blue}
        top = {'top': 1, 'top_color': self.blue}
        left = {'left': 1, 'left_color': self.blue}
        right = {'right': 1, 'right_color': self.blue}
        indented = {'indent': 1}

        left_fmt = self.add_format({**default, **left})
        left_fmt_indent = self.add_format({**default, **left, **indented})
        right_fmt = self.add_format({**default, **right})
        left_top = self.add_format({**top, **left, **default})
        left_top_right = self.add_format({**top, **left, **right, **default})
        left_top_right_indent = self.add_format({
            **top, **left, **right, **default, **indented
        })
        default_fmt = self.add_format(default)
        input_fmt = self.add_format(input_)
        input_right = self.add_format({**input_, **right})
        left_bottom_right = self.add_format(
            {**default, **bottom, **left, **right}
        )

        left_right = self.add_format({**left, **right, **default})

        self.spacer_row(73)
        self.ws.set_row(74, 13.7)
        self.ws.merge_range(
            74, 0, 74, 1, 'Visum Auftraggebende Person', left_top_right)
        self.ws.merge_range(
            74, 2, 74, 4, 'Visum Übersetzende/r', left_top_right_indent
        )
        self.ws.merge_range(74, 5, 74, 7, '', left_top_right)

        self.ws.merge_range(75, 0, 75, 1, '', left_right)
        self.ws.merge_range(75, 2, 75, 4, '', left_right)
        self.ws.merge_range(75, 5, 75, 7, '', left_right)

        self.ws.write(76, 0, 'Datum', left_fmt)
        self.ws.write(76, 1, '', input_right)
        self.ws.write(76, 2, 'Datum', left_fmt_indent)
        self.ws.write(76, 3, '', input_fmt)
        self.ws.write(76, 4, '', right_fmt)
        self.ws.merge_range(76, 5, 76, 7, '', left_right)
        self.spacer_row(77)
        self.ws.merge_range(77, 0, 77, 1, '', left_bottom_right)
        self.ws.merge_range(77, 2, 77, 4, '', left_bottom_right)
        self.ws.merge_range(77, 5, 77, 7, '', left_bottom_right)

        self.ws.write(78, 0, 'Original:', left_top)
        self.ws.merge_range(
            78, 1, 78, 7,
            'Amtsleiter oder Finanzverantwortlicher '
            '(zwecks Kontierung der Zahlungsanweisung an Personalamt)',
            right_fmt
        )
        self.ws.write(79, 0, 'Kopie:', left_fmt)
        self.ws.merge_range(79, 1, 79, 2, 'Übersetzende/r', default_fmt)
        self.ws.merge_range(79, 3, 79, 7, self.translator.title, right_fmt)

        self.ws.write(80, 0, '', left_fmt)
        self.ws.merge_range(80, 1, 80, 2, 'Auftraggebende Person', default_fmt)
        self.ws.merge_range(
            80, 3, 80, 7, '=IF(ISBLANK(C11), "", C11)', right_fmt)

        self.spacer_row(81)
        self.ws.merge_range(81, 0, 81, 7, '', left_bottom_right)

    def create_off_page_content(self):
        self.write('I13', 'Auszug aus der Übersetzungsverordnung (BGS 161.15)')

    def create_document(self, protect_pw=None):
        self.set_page_layout()
        self.write_formulas()
        self.create_header()
        current_row = self.create_table(row=14)
        self.create_footer()
        self.create_off_page_content()

        if protect_pw:
            self.protect_with(protect_pw)
        self.wb.close()
        self.file.seek(0)
        return self.file
