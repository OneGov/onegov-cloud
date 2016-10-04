var datetimepicker_i18n = {
    de_CH: {
        dayOfWeekStart: 1, // Monday
        dateformat: 'd.m.Y',
        dateformat_momentjs: 'DD.MM.YYYY',
        datetimeformat: 'd.m.Y H:i',
        datetimeformat_momentjs: 'DD.MM.YYYY HH:mm',
        placeholder_date: 'TT.MM.JJJJ',
        placeholder_datetime: 'TT.MM.JJJJ',
        lang: 'de'
    },
    it_CH: {
        dayOfWeekStart: 1,
        dateformat: 'd.m.Y',
        dateformat_momentjs: 'DD.MM.YYYY',
        datetimeformat: 'd.m.Y H:i',
        datetimeformat_momentjs: 'DD.MM.YYYY HH:mm',
        placeholder_date: 'gg.mm.aaaa',
        placeholder_datetime: 'gg.mm.aaaa oo:mm',
        lang: 'it'
    },
    fr_CH: {
        dayOfWeekStart: 1,
        dateformat: 'd.m.Y',
        dateformat_momentjs: 'DD.MM.YYYY',
        datetimeformat: 'd.m.Y H:i',
        datetimeformat_momentjs: 'DD.MM.YYYY HH:mm',
        placeholder_date: 'jj.mm.aaaa',
        placeholder_datetime: 'jj.mm.aaaa hh:mm',
        lang: 'fr'
    },
    rm_CH: {
        dayOfWeekStart: 1,
        dateformat: 'd-m-Y',
        dateformat_momentjs: 'DD-MM-YYYY',
        datetimeformat: 'd-m-Y H:i',
        datetimeformat_momentjs: 'DD-MM-YYYY HH:mm',
        placeholder_date: 'dd-mm-oooo',
        placeholder_datetime: 'dd-mm-oooo uu:mm',
        lang: 'rm'
    }
};

var convert_date = function(value, from_format, to_format) {
    if (value) {
        var as_date = moment(value, from_format).toDate();
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

var attach_button = function(input) {
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

    grid.insertBefore(input);
    input.detach().appendTo(grid.find('.' + large_column));
    button.appendTo(grid.find('.' + small_column));

    // toggle the datetime picker when clicking on the button
    button.click(function(e) {
        if (input.data('visible')) {
            input.datetimepicker('hide');
        } else {
            input.datetimepicker('show');
        }

        e.preventDefault();
        return false;
    });
};

var setup_datetimepicker = function(type) {
    var locale = get_locale();
    var i18n_options = datetimepicker_i18n[locale];
    var selector = 'input[type=' + type + ']';

    var type_specific = {
        date: {
            timepicker: false,
            format: i18n_options.dateformat,
            placeholder: i18n_options.placeholder_date,
            server_to_client: function(value) {
                return convert_date(value, 'YYYY-MM-DD', i18n_options.dateformat);
            },
            client_to_server: function(value) {
                return convert_date(value, i18n_options.dateformat_momentjs, 'Y-m-d');
            }
        },
        datetime: {
            timepicker: true,
            format: i18n_options.datetimeformat,
            placeholder: i18n_options.placeholder_datetime,
            server_to_client: function(value) {
                return convert_date(value, 'YYYY-MM-DD HH:mm', i18n_options.datetimeformat);
            },
            client_to_server: function(value) {
                return convert_date(value, i18n_options.datetimeformat_momentjs, 'Y-m-d H:i:00');
            }
        }
    }[type];

    var general = {
        allowBlank: true,
        lazyInit: false,
        dayOfWeekStart: i18n_options.dayOfWeekstart,
        lang: i18n_options.lang,
        onShow: function(_current_time, $input) {
            this.setOptions({
                value: $input.val()
            });

            $input.data('visible', true);

            setTimeout(function() {
                $('.xdsoft_datetimepicker').trigger('afterOpen.xdsoft');
            }, 50);
        },
        onSelectDate: function(_current_time, $input) {
            $input.data('visible', false);
        },
        onClose: function(_current_time, $input) {
            // we have to delay setting the visible flag slightly, otherwise
            // clicking on the button when the picker is visible leads to
            // it being hidden and shown again immediately.
            setTimeout(function() {
                $input.data('visible', false);
            }, 500);
        }
    };

    $(selector).each(function() {
        var input = $(this);

        attach_button(input);

        input.datetimepicker($.extend(
            general,
            type_specific
        ));

        // convert the initial value to the localized format
        input.attr('placeholder', type_specific.placeholder);
        input.val(type_specific.server_to_client(input.val()));

        // remove all default on-focus events, to only show the picker when
        // clicking on the button
        input.unbind();
    });

    $('form').submit(function() {
        $(this).find(selector).each(function() {
            $(this).val(type_specific.client_to_server($(this).val()));
            return true;
        });
        return true;
    });
};

// load the datepicker for date inputs if the browser does not support it
if (!Modernizr.inputtypes.date) {
    setup_datetimepicker('date');
}

// load the datetimepicker for date inputs if the browser does not support it
if (!Modernizr.inputtypes.datetime) {
    setup_datetimepicker('datetime');
}
