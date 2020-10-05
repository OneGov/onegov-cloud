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
    default_row_height = 20     # 4.5mm
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
        'align': 'center'
    }
    """
    write a number ws.write_number
    ws.write_boolean
    ws.write_row    
    """

    def __init__(self, request, translator):
        self.request = request
        self.translator = translator
        self.file = BytesIO()
        self.wb = Workbook(self.file)
        self.ws = self.wb.add_worksheet()
        self.layout = DefaultLayout(translator, request)

        # Formats
        self.cell_fmt = self.wb.add_format(self.default_fmt)
        self.title_fmt = self.add_format({
            'font_size': self.title_font_size, 'bold': True
        })
        self.editable_fmt = self.add_format({
            'bg_color': self.edit_color, 'locked': False
        })

        self.thead_blue = self.add_format({
                'bold': True,
                'font_size': self.subheader_font_size,
                'font_color': self.white,
                'bg_color': self.blue
        })
        self.thead_green = self.add_format({
                'bold': True,
                'font_size': self.subheader_font_size,
                'font_color': self.white,
                'bg_color': self.green
        })

        self.thead_lightgreen = self.add_format({
            'bold': True,
            'font_size': self.subheader_font_size,
            'bg_color': self.light_green
        })

        self.tsubhead = self.add_format({'bg_color': self.lila})
        self.tsubhead_italic = self.add_format({'bg_color': self.lila})

        self.input_time_fmt = self.add_format(
            {'num_format': 'HH:MM', 'bg_color': self.edit_color})
        self.input_date_fmt = self.add_format(
            {'num_format': 'TT.MM.JJJJ', 'bg_color': self.edit_color})

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
        options = {}
        self.ws.protect(password, options)

    def set_col_widths(self, widths, start=0):
        # set the row widths starting from left side
        for col, width in enumerate(widths, start):
            self.ws.set_column(col, col, width)

    def set_page_layout(self):
        self.ws.set_default_row(self.default_row_height)
        self.ws.set_paper(9)   # A4
        # center fpr printing
        self.ws.center_horizontally()

        # set print area
        self.ws.print_area('A1:H85')
        # self.ws.fit_to_pages(1, 1)  # Fit to 1x1 pages.

        # set col width as mm
        self.set_col_widths(self.to_width([
            21.7, 26.3, 26.3, 22.4, 26, 31.6, 28.5, 38.3
        ]))

    def coerce_fmts(self, raw_formats, use_default=True):
        if len(raw_formats) == 1 and not use_default:
            return raw_formats[0]
        default_fmt = use_default and self.default_fmt.copy() or \
                      raw_formats.pop(0)

        for fmt in raw_formats:
            default_fmt.update(fmt)
        return default_fmt

    def add_format(self, format, use_default=True):
        return self.wb.add_format(self.coerce_fmts([format], use_default))

    def add_formats(self, formats, use_default=True):
        return self.wb.add_format(self.coerce_fmts(formats, use_default))
    
    def merge_range(self, position, data, fmt=None):
        return self.ws.merge_range(position, data, fmt)

    def write(self, position, data, fmt=None, use_default=True):
        if not fmt and use_default:
            fmt = self.cell_fmt
        self.ws.write(position, data, fmt)

    def set_logo(self):
        """
        worksheet.set_header('&L&G', {'image_left': 'logo.jpg'})
        """
        pass

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
        self.merge_range('C12:E12', None, self.editable_fmt)
        self.merge_range('C13:E13', None, self.editable_fmt)

        self.write('F10', 'Übersetzende/r')
        self.write('F10', 'Personalnummer')
        self.write('F10', 'Übers. Sprache')
        self.write('F10', 'Quellensteuer')

        self.merge_range('G10:H10', None, self.editable_fmt)
        self.merge_range('G11:H11', None, self.editable_fmt)
        self.merge_range('G12:H12', None, self.editable_fmt)

    def create_table(self, row):

        subtitles = (
            'Datum', 'von', 'bis', 'Total', '', '', 'Indstrieminuten',
            'Zwischentotal'
        )

        def headers(row, text):
            self.merge_range(f'A{row+1}:H{row+1}', text, self.thead_blue)

        def subheaders(row, col, subtitles):
            for col_ix, text in enumerate(subtitles, col):
                fmt = self.tsubhead
                if text == 'Zwischentotal':
                    fmt = self.tsubhead_italic
                self.ws.write(row, col_ix, text, fmt)

        def input_block(start_col, start_row):
            self.ws.write_blank(start_row, start_col, self.input_date_fmt)
            # self.ws.write_blank(start_row, start_col, self.input_date_fmt)

        headers(row, 'Dolmetschertätigkeit - '
                     '(§ 15 Abs. 1 lit. a, 06:00-20:00 Uhr)')
        subheaders(row + 1, 0, subtitles)

        headers(row + 5, 'Dolmetschertätigkeit - zuschlagsberechtigter '
                         'Zeitraum +25 %   '
                         '- (§ 15 Abs. 1 lit. b, 20:00-06:00)')

        headers(row + 8, 'Dolmetschertätigkeit bei ausserordentlich '
                             'schwierigen Übersetzungen - '
                             'zuschlagsberechtigter Zeitraum +25 % - '
                             '(§ 15 Abs. 1 lit. b, 20:00-06:00)')

        subheaders(row + 13, 0, (
            'Datum', 'Reiseweg in km', '', '', 'Wegpauschale', '', '',
            'Zwischentotal'))

        # subheaders(row + 6, 0, subtitles)

    def create_document(self, protect_pw=None):
        self.set_page_layout()
        self.create_header()
        self.create_table(15)

        if protect_pw:
            self.protect_with(protect_pw)
        self.wb.close()
        self.file.seek(0)
        return self.file



