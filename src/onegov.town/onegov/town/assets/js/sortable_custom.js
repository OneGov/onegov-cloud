Sortable.create($('.sidebar > ul')[0], {
    onUpdate: function(event) {
        $(event.item).addClass('flash-ok');

        setTimeout(function() {
            $(event.item).removeClass('flash-ok');
        }, 1000);
    }
});
Sortable.create($('.sidebar > ul ul')[0], {
    onUpdate: function(event) {
        $(event.item).addClass('flash-ok');

        setTimeout(function() {
            $(event.item).removeClass('flash-ok');
        }, 1000);
    }
});

$('.sidebar li').each(function(){
    this.addEventListener('dragstart', function(event) {
        event.target.className = 'dragging';
    });
});
