/*
    The reservation list uses a subset of the features of the reservation
    calendar to pick reservations from a list/table of reservations
*/

var rl = $.reservationList = {};
var defaultOptions = {
    afterSetup: [],
    /* Whether we only show wholeDay reservations */
    wholeDay: false
};

rl.events = [
    'rc-allocations-changed',
    'rc-reservation-error',
    'rc-reservations-changed'
];

rl.passEventsToList = function(_list, target, source) {
    var list = $(_list);

    _.each(rl.events, function(eventName) {
        target.on(eventName, _.debounce(function(_e, data) {
            list.trigger(eventName, [data, _list, source]);
        }));
    });
};

rl.getOptions = function(options) {
    var rlOptions = $.extend(true, defaultOptions, options);

    // reservation selection
    rl.setupReservationSelect(rlOptions);

    return rlOptions;
};

$.fn.reservationList = function(options) {
    var rlOptions = rl.getOptions(options);

    return this.map(function(_ix, element) {

        var list = $(element);

        // handles clicks on events
        list.on('click', '.event:not(.event-unavailable)', function(e) {
            var el = $(this);
            if (!el.hasClass('event-adjustable') && el.hasClass('selected')) {
                e.preventDefault();
                return false;
            }
            var event = {
                partlyAvailable: el.data('partly-available'),
                quota: el.data('quota'),
                quotaLeft: el.data('quota-left'),
                start: moment(el.data('start')),
                end: moment(el.data('end')),
                wholeDayDefault: options.wholeDay,
                wholeDay: el.data('whole-day'),
                reserveurl: el.data('reserveurl')
            };
            rl.removeAllPopups();
            var singleSelect = !e.shiftKey && !e.altKey && !e.ctrlKey;
            if (el.hasClass('event-adjustable')) {
                rl.showActionsPopup(list, this, event, singleSelect);
            } else {
                // by default we only allow one reservation per row
                // so if we pick another one we delete the other ones
                // selected in the same row
                if (singleSelect) {
                    var delete_existing = el.data('delete');
                    if (delete_existing !== undefined) {
                        _.each(delete_existing, function(delete_link) {
                            rl.delete(list, delete_link);
                        });
                    }
                }
                rl.reserve(
                    list,
                    event.reserveurl,
                    event.start.format('hh:mm'),
                    event.end.format('hh:mm'),
                    1,
                    event.wholeDay
                );
            }
            e.preventDefault();
            return false;
        });

        for (var i = 0; i < rlOptions.afterSetup.length; i++) {
            rlOptions.afterSetup[i](list);
        }

        return list;
    });
};

// sends requests through intercooler
rl.request = function(list, url, attribute) {
    var el = $('<a />')
        .attr(attribute, url)
        .css('display', 'none')
        .appendTo($('body'));

    Intercooler.processNodes(el);

    el.on('complete.ic', function() {
        el.remove();
    });

    var source = $(list).find('.has-popup');
    rl.passEventsToList(list, el, source);

    el.click();
};

rl.delete = function(list, url) {
    rl.request(list, url, 'ic-delete-from');
};

rl.post = function(list, url) {
    rl.request(list, url, 'ic-post-to');
};

rl.reserve = function(list, url, start, end, quota, wholeDay) {
    url = new Url(url);
    url.query.start = start;
    url.query.end = end;
    url.query.quota = quota;
    url.query.whole_day = wholeDay && '1' || '0';

    rl.post(list, url.toString());
};

// popup handler implementation
rl.showActionsPopup = function(list, element, event, singleSelect) {
    var wrapper = $('<div class="reservation-actions">');
    var reservation = $('<div class="reservation-form">').appendTo(wrapper);

    // eslint-disable-next-line no-use-before-define
    ReservationForm.render(reservation.get(0), event, rl.previousReservationState, function(state) {
        // by default we only allow one reservation per row
        // so if we pick another one we delete the other ones
        // selected in the same row
        if (singleSelect) {
            var delete_existing = $(element).data('delete');
            if (delete_existing !== undefined) {
                _.each(delete_existing, function(delete_link) {
                    rl.delete(list, delete_link);
                });
            }
        }
        rl.reserve(
            list,
            event.reserveurl,
            state.start,
            state.end,
            state.quota,
            state.wholeDay
        );
        $(this).closest('.popup').popup('hide');
    });

    rl.showPopup(list, element, wrapper);
};

rl.showErrorPopup = function(list, element, message) {
    rl.showPopup(list, element, message, 'top', ['error']);
};

rl.showPopup = function(list, element, content, position, extraClasses) {

    $(element).closest('.event').addClass('has-popup');

    var options = {
        autoopen: true,
        tooltipanchor: element,
        type: 'tooltip',
        onopen: function() {
            rl.onPopupOpen.call(this, list);
            setTimeout(function() {
                $(window).trigger('resize');
            }, 0);
        },
        onclose: function() {
            $(element).closest('.event').removeClass('has-popup');
        },
        closebutton: true,
        closebuttonmarkup: '<a href="#" class="close">×</a>'
    };

    switch (position || 'right') {
        case 'top':
            options.horizontal = 'center';
            options.vertical = 'top';
            options.extraClasses = _.union(['top'], extraClasses || []);
            options.offsettop = -5;
            break;
        case 'right':
            options.horizontal = 'right';
            options.vertical = 'middle';
            options.extraClasses = _.union(['right'], extraClasses || []);
            options.offsetleft = -10;
            break;
        default:
            throw Error("Unknown position: " + position);
    }

    $('<div class="popup" />').append(content).popup(options);
};

rl.onPopupOpen = function(list) {
    var popup = $(this);
    var options = popup.data('popupoptions');

    _.each(options.extraClasses, function(className) {
        popup.addClass(className);
    });

    var links = popup.find('a:not(.internal)');

    // hookup all links with intercool
    links.each(function(_ix, link) {
        Intercooler.processNodes($(link));
    });

    // close the popup after any click on a link
    _.each(['ic.success', 'mouseup'], function(eventName) {
        $(links).on(eventName, _.debounce(function() {
            popup.popup('hide');
        }));
    });

    // hookup the confirmation dialog
    var confirm_links = popup.find('a.confirm');
    confirm_links.confirmation();

    // pass all reservationlist events to the list
    rl.passEventsToList(list, links, options.tooltipanchor);
};

rl.removeAllPopups = function() {
    $('.popup').popup('hide').remove();
};

// add ie-cache busting to url
rl.bustIECache = function(originalUrl) {
    var url = new Url(originalUrl);
    url.query['ie-cache'] = (new Date()).getTime();
    return url.toString();
};

rl.updateReservations = function(list, reservationform, data) {
    // eslint-disable-next-line no-use-before-define
    ReservationSelection.render(
        list.siblings('.reservation-selection').get(0),
        list,
        data.reservations,
        data.delete_link,
        data.prediction,
        reservationform
    );

    // clear list state
    list.find('.event').removeClass(['selected', 'not-selected'])
        .removeAttr('data-delete');

    /* eslint-disable max-nested-callbacks */
    // determine list state
    var rows = [];
    list.find('tbody tr').each(function(index, element) {
        rows[index] = {
            row: $(element),
            // which elements to mark as selected
            selected: [],
            // which reservations to delete when changing
            // the selection
            reservations: []
        };
    });
    _.each(data.reservations, function(reservation) {
        var resource = reservation.resource;
        var isodate = reservation.date.substring(0, 10);
        var column = list.find('th[data-resource="' + resource + '"]').index();
        var row = list.find('tr[data-date="' + isodate + '"]');
        var events = row.children().eq(column).find('.event');
        var selected = null;
        if (events.length === 1) {
            selected = events.eq(0);
        } else {
            var target_start = moment(reservation.date);
            var target_end = moment(target_start)
                .set('hour', parseInt(reservation.time.substring(8, 10), 10))
                .set('minute', parseInt(reservation.time.substring(11), 10));
            events.filter(':not(.event-adjustable)').each(function() {
                var event = $(this);
                if (!target_start.isSame(event.data('start'))) {
                    return;
                }
                if (target_end.isSame(event.data('end'))) {
                    selected = event;
                }
            });

            if (selected === null) {
                events.filter('.event-adjustable').each(function() {
                    var event = $(this);
                    if (target_start.isBefore(event.data('start'))) {
                        return;
                    }
                    if (!target_end.isAfter(event.data('end'))) {
                        selected = event;
                    }
                });
            }
        }
        // record selected event
        if (selected !== null) {
            var row_data = rows[row.index()];
            row_data.reservations.push(reservation.delete);
            if (column >= 0) {
                row_data.selected.push(selected);
            }
        }
    });

    // set list state
    _.each(rows, function(row_data) {
        if (row_data.reservations.length === 0) {
            return;
        }
        row_data.row.find('.event')
            .removeClass('selected')
            .addClass('not-selected')
            .data('delete', row_data.reservations);

        _.each(row_data.selected, function(selected) {
            selected.removeClass('not-selected').addClass('selected');
        });
    });
    /* eslint-enable max-nested-callbacks */
    rl.loadPreviousReservationState(data.reservations);
};

// takes the loaded reservations and deduces the previous state from them
rl.loadPreviousReservationState = function(reservations) {
    if (reservations.length > 0) {
        reservations = _.sortBy(reservations, function(reservation) {
            return reservation.created;
        });

        for (var i = reservations.length - 1; i >= 0; i--) {
            if (reservations[i].time.match(/^\d{2}:\d{2} - \d{2}:\d{2}$/)) {
                rl.previousReservationState = {
                    'start': reservations[i].time.split(' - ')[0],
                    'end': reservations[i].time.split(' - ')[1]
                };

                break;
            }
        }
    } else {
        rl.previousReservationState = {};
    }
};

// setup the reservation selection on the right
rl.setupReservationSelect = function(options) {
    options.afterSetup.push(function(list) {
        var view = $(list);

        var selection = $('<div class="reservation-selection"></div>')
            .insertAfter(view);
        $('<div class="clearfix"></div>').insertAfter(selection);

        list.on('rc-reservation-error', function(_e, data, _list, target) {
            var event = list.find('.has-popup');

            if (!target || target.length === 0) {
                if (event.length !== 0) {
                    target = event;
                } else {
                    target = list.find('tbody');
                }
            }

            target = target || list.find('.has-popup') || list.find('.fc-view');
            rl.showErrorPopup(list, target, data.message);
        });

        list.on('rc-reservations-changed', function() {
            $.getJSON(rl.bustIECache(options.reservations), function(data) {
                rl.updateReservations(list, options.reservationform, data);
            });
        });

        list.trigger('rc-reservations-changed');
    });
};

rl.roundNumber = function(num) {
    return +Number(Math.round(num + "e+2") + "e-2");
};

/*
    Shows the list of reservations to be confirmed.
*/
var ReservationSelection = React.createClass({
    handleClick: function(reservation) {
        rl.delete($(this.props.list), reservation.delete);
    },
    handleSubmit: function() {
        if (this.props.reservations.length) {
            window.location = this.props.reservationform;
        }
    },
    handleRemoveAll: function() {
        if (this.props.reservations.length && this.props.delete_link) {
            var list = $(this.props.list);
            var reservationform = this.props.reservationform;
            $.ajax({
                url: this.props.delete_link,
                dataType: 'json',
                method: 'DELETE',
                success: function(data) {
                    rl.updateReservations(list, reservationform, data);
                }
            });
        }
    },
    handleGotoDate: function(isodate) {
        var row = $(this.props.list).find('tr[data-date="' + isodate + '"]');
        if (row.length !== 0) {
            row[0].scrollIntoView();
        }
    },
    render: function() {
        var self = this;

        return (
            <div className="reservation-selection-inner">
                <h3>{locale("Dates")}</h3>
                {
                    this.props.reservations.length === 0 &&
                        <p>{locale("Select allocations in the list to reserve them")}</p>
                }
                {this.props.reservations.length > 8 && (
                    <div>
                        <a onClick={self.handleRemoveAll} role="button" className={this.props.reservations.length === 0 && 'disabled button secondary' || 'button alert'}>
                            {locale("Remove all")}
                        </a>
                        <a onClick={self.handleSubmit} role="button" className={this.props.reservations.length === 0 && this.props.delete_link && 'disabled button secondary' || 'button'}>
                            {locale("Reserve")}
                        </a>
                    </div>
                )}
                {
                    this.props.reservations.length > 0 &&
                        <ul>{
                            _.map(this.props.reservations, function(r, ix) {
                                var date = moment(r.date).locale(window.locale.language);
                                var boundClick = self.handleClick.bind(self, r);
                                var boundGotoDate = self.handleGotoDate.bind(self, r.date.substring(0, 10));
                                return (
                                    <li key={ix} className="reservation">
                                        <span className="reservation-date" data-quota={r.quota}>
                                            <a onClick={boundGotoDate} title={locale('Goto date')} role="link">
                                                {date.format('ddd LL')}
                                            </a>
                                            {r.warning && (
                                                <span className="reservation-warning" title={r.warning}>
                                                    <i className="fa fa-clock-o" aria-hidden="true" />
                                                </span>
                                            )}
                                        </span>
                                        <span className="reservation-resource">{r.title}</span>
                                        <span className="reservation-time">{r.time}</span>
                                        {r.price && (
                                            <span className="reservation-price">
                                                {r.price.amount.toFixed(2)} {r.price.currency}
                                            </span>
                                        )}
                                        <a className="delete" onClick={boundClick} role="button">{locale('Remove')}</a>
                                    </li>
                                );
                            })
                        }</ul>
                }
                <a onClick={self.handleRemoveAll} role="button" className={this.props.reservations.length === 0 && 'disabled button secondary' || 'button alert'}>
                    {locale("Remove all")}
                </a>
                <a onClick={self.handleSubmit} role="button" className={this.props.reservations.length === 0 && this.props.delete_link && 'disabled button secondary' || 'button'}>
                    {locale("Reserve")}
                </a>
            </div>
        );
    }
});

ReservationSelection.render = function(element, list, reservations, delete_link, prediction, reservationform) {
    ReactDOM.render(
        <ReservationSelection
            list={list}
            reservations={reservations}
            reservationform={reservationform}
            delete_link={delete_link}
            prediction={prediction}
        />,
        element);
};

/*
    Allows to fine-adjust the reservation before adding it.
*/
var ReservationForm = React.createClass({
    getInitialState: function() {
        var state = {
            quota: 1
        };

        // when this is set all events are fully available
        if (this.props.wholeDayDefault) {
            state.start = "";
            state.end = "";
            state.wholeDay = true;
        } else {
            state.start = this.props.start.format('HH:mm');
            state.end = this.props.end.format('HH:mm');
            state.wholeDay = false;
        }

        state.end = state.end === '00:00' && '24:00' || state.end;

        return state;
    },
    componentDidMount: function() {
        var node = $(ReactDOM.findDOMNode(this));
        // by default we focus the first input
        var selector = 'input:first';
        if (!this.props.wholeDayDefault && this.props.partlyAvailable && this.props.wholeDay) {
            // in this case we focus the first time input instead
            selector = 'input[type="time"]:first';
        }

        // the timeout is set to 100ms because the popup will do its own focusing
        // after 50ms (we could use it, but we want to focus AND select)
        setTimeout(function() {
            node.find(selector).focus().select();
        }, 100);
    },
    handleInputChange: function(e) {
        var state = _.extend({}, this.state);
        var name = e.target.getAttribute('name');

        switch (name) {
            case 'reserve-whole-day':
                state.wholeDay = e.target.value === 'yes';
                break;
            case 'start':
                state.start = e.target.value;
                break;
            case 'end':
                state.end = e.target.value === '00:00' && '24:00' || e.target.value;
                break;
            case 'count':
                state.quota = parseInt(e.target.value, 10);
                break;
            default:
                throw Error("Unknown input element: " + name);
        }

        this.setState(state);
    },
    handleButton: function(e) {
        var node = ReactDOM.findDOMNode(this);
        var self = this;

        $(node).find('input').each(function(_ix, el) {
            $(el).blur();
        });

        setTimeout(function() {
            self.props.onSubmit.call(node, self.state);
        }, 0);

        e.preventDefault();
    },
    handleSetPreviousTime: function(e) {
        var previousState = this.props.previousReservationState;
        var node = $(ReactDOM.findDOMNode(this));
        var inputs = node.find('[name="start"],[name="end"]');

        $(inputs[0]).val(previousState.start);
        $(inputs[1]).val(previousState.end);

        // deselect 'whole-day' if it exists
        node.find('[name="reserve-whole-day"]').filter('[value="no"]').prop('checked', true);

        // briefly highlight the inputs
        inputs.addClass('highlighted');
        setTimeout(function() {
            inputs.removeClass('highlighted');
        }, 500);

        var state = _.extend({}, this.state);
        state.start = previousState.start;
        state.end = previousState.end;
        state.wholeDay = false;

        this.setState(state);

        e.preventDefault();
    },
    handleTimeInputFocus: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.target.select();
            e.preventDefault();
        }
    },
    handleTimeInputMouseUp: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.preventDefault();
        }
    },
    handleTimeInputBlur: function(e) {
        if (!Modernizr.inputtypes.time) {
            e.target.value = OneGov.utils.inferTime(e.target.value);
            this.handleInputChange(e);
        }
    },
    parseTime: function(date, time) {
        time = OneGov.utils.inferTime(time);

        if (!time.match(/^[0-2]{1}[0-9]{1}:?[0-5]{1}[0-9]{1}$/)) {
            return null;
        }

        var hour = parseInt(time.split(':')[0], 10);
        var minute = parseInt(time.split(':')[1], 10);

        if (hour < 0 || 24 < hour) {
            return null;
        }

        if (minute < 0 || 60 < minute) {
            return null;
        }

        date.hour(hour);
        date.minute(minute);

        return date;
    },
    isValidStart: function(start) {
        var startdate = this.parseTime(this.props.start.clone(), start);
        return startdate !== null && this.props.start <= startdate;
    },
    isValidEnd: function(end) {
        var enddate = this.parseTime(this.props.start.clone(), end);
        return enddate !== null && enddate <= this.props.end;
    },
    isValidQuota: function(quota) {
        return quota > 0 && quota <= this.props.quotaLeft;
    },
    isValidState: function() {
        if (this.props.partlyAvailable) {
            if (this.props.wholeDay && this.state.wholeDay) {
                return true;
            } else {
                return this.isValidStart(this.state.start) && this.isValidEnd(this.state.end);
            }
        } else {
            return this.isValidQuota(this.state.quota);
        }
    },
    // eslint-disable-next-line complexity
    render: function() {
        var buttonEnabled = this.isValidState();
        var showWholeDay = this.props.partlyAvailable && this.props.wholeDay;
        var showTimeRange = this.props.partlyAvailable && (!this.props.wholeDay || !this.state.wholeDay);
        var hasPreviousTimeToOffer = !_.isEmpty(this.props.previousReservationState) &&
            (
                this.props.previousReservationState.start !== this.state.start ||
                this.props.previousReservationState.end !== this.state.end
            );

        var showPreviousTime = (showTimeRange || showWholeDay) && hasPreviousTimeToOffer;
        var showQuota = !this.props.partlyAvailable;

        return (
            <form>
                {showWholeDay && (
                    <div className="field">
                        <span className="label-text">{locale("Whole day")}</span>

                        <input id="reserve-whole-day-yes"
                            name="reserve-whole-day"
                            type="radio"
                            value="yes"
                            checked={this.state.wholeDay}
                            onChange={this.handleInputChange}
                        />
                        <label htmlFor="reserve-whole-day-yes">{locale("Yes")}</label>
                        <input id="reserve-whole-day-no"
                            name="reserve-whole-day"
                            type="radio"
                            value="no"
                            checked={!this.state.wholeDay}
                            onChange={this.handleInputChange}
                        />
                        <label htmlFor="reserve-whole-day-no">{locale("No")}</label>
                    </div>
                )}

                {showTimeRange && (
                    <div className="field split">
                        <div>
                            <label htmlFor="start">{locale("From")}</label>
                            <input name="start" type="time" size="4"
                                defaultValue={this.state.start}
                                onChange={this.handleInputChange}
                                onFocus={this.handleTimeInputFocus}
                                onMouseUp={this.handleTimeInputMouseUp}
                                onBlur={this.handleTimeInputBlur}
                                className={this.isValidStart(this.state.start) && 'valid' || 'invalid'}
                            />
                        </div>
                        <div>
                            <label htmlFor="end">{locale("Until")}</label>
                            <input name="end" type="time" size="4"
                                defaultValue={this.state.end}
                                onChange={this.handleInputChange}
                                onFocus={this.handleTimeInputFocus}
                                onMouseUp={this.handleTimeInputMouseUp}
                                onBlur={this.handleTimeInputBlur}
                                className={this.isValidEnd(this.state.end) && 'valid' || 'invalid'}
                            />
                        </div>
                    </div>
                )}

                {showPreviousTime && (
                    <a href="#" onClick={this.handleSetPreviousTime} className="select-previous-time internal">
                        <i className="fa fa-chevron-circle-right" aria-hidden="true" />
                        <span>{this.props.previousReservationState.start}</span>
                        <span>&nbsp;-&nbsp;</span>
                        <span>{this.props.previousReservationState.end}</span>
                    </a>
                )}

                {showQuota && (
                    <div className="field">
                        <div>
                            <label htmlFor="count">{locale("Count")}</label>
                            <input name="count" type="number" size="4"
                                min="1"
                                max={this.props.quotaLeft}
                                defaultValue={this.state.quota}
                                onChange={this.handleInputChange}
                            />
                        </div>
                    </div>
                )}

                <button className={buttonEnabled && "button" || "button secondary"} disabled={!buttonEnabled} onClick={this.handleButton}>{locale("Add")}</button>
            </form>
        );
    }
});

ReservationForm.render = function(element, event, previousReservationState, onSubmit) {

    ReactDOM.render(
        <ReservationForm
            partlyAvailable={event.partlyAvailable}
            quota={event.quota}
            quotaLeft={event.quotaLeft}
            start={event.start}
            end={event.end}
            wholeDay={event.wholeDay}
            wholeDayDefault={event.wholeDayDefault}
            previousReservationState={previousReservationState}
            onSubmit={onSubmit}
        />,
        element);
};
