var datetimepicker_i18n = {
    de_CH: {
        dayOfWeekStart: 1, // Monday
        format: 'd.m.Y',
        placeholder: 'TT.MM.JJJJ',
        lang: 'de'
    },
    it_CH: {
        dayOfWeekStart: 1,
        format: 'd.m.Y',
        placeholder: 'gg.mm.aaaa',
        lang: 'it'
    },
    fr_CH: {
        dayOfWeekStart: 1,
        format: 'd.m.Y',
        placeholder: 'jj.mm.aaaa',
        lang: 'fr'
    },
    rm_CH: {
        dayOfWeekStart: 1,
        format: 'd-m-Y',
        placeholder: 'dd-mm-oooo',
        lang: 'rm'
    }
};

var convert_date = function(value, from_format, to_format) {
    if (value) {
        var as_date = Date.parseDate(value, from_format);
        if (as_date) {
            return as_date.dateFormat(to_format);
        }
    }
    return value;
};

var get_locale = function() {
    var locale = $('html').attr('lang');
    if (locale) {
        return locale.replace('-', '_');
    } else {
        return 'de_CH';
    }
};

// load the datetimepicker for date inputs if the browser does not support it
if (!Modernizr.inputtypes.date) {
    var _locale = get_locale();

    $('input[type=date]').each(function() {
        var input = $(this);
        var large_column = 'small-11';
        var small_column = 'small-1';

        if (input.is('.small')) {
            large_column = 'small-10';
            small_column = 'small-2';
        }

        // inject a button with which to launch the datetime picker
        var button = $('<a href="#" role="presentation" tabindex="-1" class="button secondary postfix datetimepicker"><i class="fa fa-calendar"></i></a>');
        var grid = $([
            '<div class="row collapse">',
            '<div class="' + large_column + ' columns"></div>',
            '<div class="' + small_column + ' columns"></div>',
            '</div>'
        ].join(''));

        var visible = false;

        grid.insertBefore(input);
        input.detach().appendTo(grid.find('.' + large_column));
        button.appendTo(grid.find('.' + small_column));

        // hide/show the datetime picker when clicking on the button
        button.click(function(e) {
            if (visible) {
                input.datetimepicker('hide');
            } else {
                input.datetimepicker('show');
            }

            e.preventDefault();
            return false;
        });

        input.datetimepicker({
            allowBlank: true,
            lazyInit: false,
            timepicker: false,
            dayOfWeekStart: datetimepicker_i18n[_locale].dayOfWeekStart,
            format: datetimepicker_i18n[_locale].format,
            lang: datetimepicker_i18n[_locale].lang,
            onShow: function(_current_time, $input) {
                this.setOptions({
                    value: $input.val()
                });

                visible = true;
            },
            onSelectDate: function() {
                visible = false;
            },
            onClose: function() {
                // we have to delay setting the visible flag slightly, otherwise
                // clicking on the button when the picker is visible leads to
                // it being hidden and shown again immediately.
                setTimeout(function() {
                    visible = false;
                }, 500);
            }
        });

        // remove all default on-focus events, to only show the picker when
        // clicking on the button
        input.unbind();

        input.attr('placeholder', datetimepicker_i18n[_locale].placeholder);
        input.val(convert_date(input.val(), 'Y-m-d', datetimepicker_i18n[_locale].format));
    });

    $('form').submit(function() {
        $(this).find('input[type=date]').each(function() {
            $(this).val(convert_date($(this).val(), datetimepicker_i18n[_locale].format, 'Y-m-d'));
            return true;
        });
        return true;
    });
}
