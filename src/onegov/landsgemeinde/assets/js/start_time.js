$(document).ready(function(){
    // when #state-1 is clicked log the current time
    $('#state-1').click(function(){
        var now = new Date();
        var hour =  now.getHours().toString().padStart(2, '0');
        var minute =  now.getMinutes().toString().padStart(2, '0');
        var second =  now.getSeconds().toString().padStart(2, '0');
        now = hour + ':' + minute + ':' + second;
        console.log('2 Start time 2:', now);

        // insert the current time into #start_time if there is no value
        if ($('#start_time').val() == '') {
            console.log('Inserting start time:', now);
            $('#start_time').val(now);
        }
    });
})
