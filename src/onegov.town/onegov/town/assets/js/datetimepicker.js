// load the datetimepicker for date inputs if the browser does not support it
if (!Modernizr.inputtypes.date) {
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

    var locale = $('html').attr('lang');
    if (locale) {
        locale = locale.replace('-', '_');
        if (!(locale in datetimepicker_i18n)) {
            locale = 'de_CH';
        }
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
        var input = $(this);

        // inject a button with which to launch the datetime picker
        var button = $('<a href="#" class="button postfix datetimepicker"><i class="fa fa-calendar"></i></a>');
        var grid = $([
            '<div class="row collapse">',
            '<div class="small-11 columns"></div>',
            '<div class="small-1 columns"></div>',
            '</div>'
        ].join(''));

        var visible = false;

        input.closest('.columns').append(grid);
        input.detach().appendTo(grid.find('.small-11'));
        button.appendTo(grid.find('.small-1'));

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
            dayOfWeekStart: datetimepicker_i18n[locale].dayOfWeekStart,
            format: datetimepicker_i18n[locale].format,
            lang: datetimepicker_i18n[locale].lang,
            onShow: function (current_time, $input) {
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

        input.attr('placeholder', datetimepicker_i18n[locale].placeholder);
        input.val(convert_date(input.val(), 'Y-m-d', datetimepicker_i18n[locale].format));
    });

    $('form').submit(function(event) {
        $(this).find('input[type=date]').each(function() {
            $(this).val(convert_date($(this).val(), datetimepicker_i18n[locale].format, 'Y-m-d'));
            return true;
        });
        return true;
    });
}
