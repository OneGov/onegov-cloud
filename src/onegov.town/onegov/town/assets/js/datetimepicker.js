// load the datetimepicker for date inputs if the browser does not support it
if (!Modernizr.inputtypes.date) {
    var datetimepicker_i18n = {
    		de_CH: {
            dayOfWeekStart: 1, // Monday
            format: 'd.m.Y',
            placeholder: 'TT.MM.JJJJ',
            lang: 'de',
        }
    };

    var locale = $('html').attr('lang');
    if (locale ) {
        locale = locale.replace('-', '_');
    } else {
        locale = 'de_CH';
    }

    var convert_date = function(value, from_format, to_format) {
        if (value) {
            var as_date = Date.parseDate(value, from_format);
            if (as_date) {
                return as_date.dateFormat(to_format);
            }
        }
        return value;
    };

    $('input[type=date]').each(function() {
        $(this).datetimepicker({
            allowBlank: true,
            lazyInit: false,
            timepicker: false,
            dayOfWeekStart: datetimepicker_i18n[locale].dayOfWeekStart,
            format: datetimepicker_i18n[locale].format,
            lang: datetimepicker_i18n[locale].lang,
        });
        $(this).attr('placeholder', datetimepicker_i18n[locale].placeholder);
        $(this).val(convert_date($(this).val(), 'Y-m-d', datetimepicker_i18n[locale].format));
    });

    $('form').submit(function(event) {
        $(this).find('input[type=date]').each(function() {
            $(this).val(convert_date($(this).val(), datetimepicker_i18n[locale].format, 'Y-m-d'));
            return true;
        });
        return true;
    });
}
