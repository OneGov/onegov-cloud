
render_count = function(count) {
    return '(' + count + ')';
};

$('input[data-max-length],textarea[data-max-length]').each(function() {
    var $this = $(this);
    var counter_id = $this.attr('id') + '-counter';
    var max_length = $this.attr('data-max-length');
    var counter_element = document.createElement('SPAN');
    counter_element.innerHTML = render_count(max_length - this.value.length);
    counter_element.setAttribute("id", counter_id);
    this.before(counter_element);

    // Register event listener
    $this.keyup(function() {
        var el = $('#' + counter_id);
        el.html(render_count(max_length - this.value.length));
        if ((max_length - this.value.length) < 0) {
            el.css('color', '#FF0000');
        } else {
            el.removeAttr('style');
        }
    });
});
