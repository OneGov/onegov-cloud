// Global functions namespace
OneGov = {
    utils: {

    }
};

// generic function for parsing date fragments (like '0900' or '9:00')
// and returning the same fragment in hh:mm format
OneGov.utils.inferTime = function(time) {
    var numeric = time.replace(/[.:\-/]+/g, '');
    var int = function(num) { return parseInt(num, 10); };

    if (numeric.match(/^\d{1}$/)) {
        numeric = '0' + numeric + '00';
    } else if (numeric.match(/^\d{2}$/)) {
        if (int(numeric) > 24) {
            numeric = '0' + numeric + '0';
        } else {
            numeric += '00';
        }
    } else if (numeric.match(/^\d{3}$/)) {
        if (int(numeric) > 240) {
            numeric = '0' + numeric;
        } else {
            numeric += '0';
        }
    }

    if (numeric.match(/^\d{4}$/)) {
        numeric = numeric.slice(0, 2) + ':' + numeric.slice(2, 4);
    }

    return numeric;
};
