var datetimepicker_i18n = {
    de_CH: {
        dayOfWeekStart: 1, // Monday
        dateformat: 'd.m.Y',
        dateformat_momentjs: 'DD.MM.YYYY',
        datetimeformat: 'd.m.Y H:i',
        datetimeformat_momentjs: 'DD.MM.YYYY HH:mm',
        placeholder_date: 'TT.MM.JJJJ',
        placeholder_datetime: 'TT.MM.JJJJ hh:mm',
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

var setup_datetimepicker = function(type, selector, onChange, extraOptions) {
    var locale = get_locale();
    var i18n_options = datetimepicker_i18n[locale];

    extraOptions = extraOptions || {};
    onChange = onChange || function() {};
    selector = selector || 'input[type=' + type + ']';

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
        },
        'datetime-local': {
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

    var onSelect = function(_current_time, $input) {
        $input.data('visible', false);

        // send a mock-event to the given onchange handler (used for react
        // integration)
        onChange({
            target: $input.get(0),
            preventDefault: function() {}
        });

        // trigger intercooler requests if any
        Intercooler.triggerRequest($input);

        // there's a bug where the placeholder stays in the input field
        // even though an input is already being shown. This is the sledge-
        // hammer method of working around that issue:
        if (type === 'datetime') {
            var placeholder = $input.attr('placeholder');
            $input.attr('placeholder', '');
            _.defer(function() {
                $input.attr('placeholder', placeholder);
            });
        }
    };

    var general = {
        allowBlank: true,
        lazyInit: false,
        dayOfWeekStart: i18n_options.dayOfWeekStart,
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
        onSelectDate: onSelect,
        onSelectTime: onSelect,
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

        if (input.data('is-attached') === true) {
            return;
        }

        attach_button(input);

        input.datetimepicker($.extend(
            general,
            type_specific,
            extraOptions
        ));

        // convert the initial value to the localized format
        input.attr('placeholder', type_specific.placeholder);
        input.val(type_specific.server_to_client(input.val()));

        // keep the date format around
        input.data('dateformat', i18n_options.datetimeformat_momentjs);

        // remove all default on-focus events, to only show the picker when
        // clicking on the button
        input.unbind();

        input.data('is-attached', true);
    });

    $('form').submit(function() {
        var form = $(this);

        if (form.data('submitted-' + selector) !== true) {
            form.data('submitted-' + selector, true);

            form.find(selector).each(function() {
                var field = $(this);
                var oldval = field.val();

                field.val(type_specific.client_to_server(oldval));

                // reset the value after submitting it, which helps with certain
                // browsers that will otherwise retain this value when pressing
                // the back button (Safari)
                _.defer(function() {
                    field.val(oldval);
                    form.data('submitted-' + selector, false);
                });

                return true;
            });
        }

        return true;
    });
};

var setupDatetimePickers = function() {
    // load the datepicker for date inputs if the browser does not support it
    if (!Modernizr.inputtypes.date) {
        setup_datetimepicker('date', null);
    }

    // load the datetimepicker for date inputs if the browser does not support it
    if (!Modernizr.inputtypes.datetime) {
        setup_datetimepicker('datetime', null);
    }

    if (!Modernizr.inputtypes['datetime-local']) {
        setup_datetimepicker('datetime-local', null);
    }

    // for time fields we only add time parsing
    if (!Modernizr.inputtypes.time) {
        $('input[type=time]').change(function() {
            $(this).val(OneGov.utils.inferTime($(this).val()));
        });
    }
};

$(document).ready(setupDatetimePickers);
$(document).on('process-common-nodes', setupDatetimePickers);
