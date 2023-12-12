document.addEventListener("DOMContentLoaded", function() {

    var lastModified;
    function reload() {
        var http = new XMLHttpRequest();
        http.open('HEAD', document.location + '?' + new Date().getTime());
        http.onreadystatechange = function() {
            if (this.readyState === this.DONE) {
                var modified = this.getResponseHeader("Last-Modified");
                if (lastModified && modified !== lastModified && this.status === 200) {
                    window.location.href = window.location.href.split('?')[0] + '?' + new Date().getTime();
                }
                lastModified = modified;
            }
        };
        http.send();
    }
    setInterval(reload, 5000);

    const next = document.body.dataset.next;
    const duration = document.body.dataset.duration;
    function cycle() {
        window.location.replace(next);
    }
    if (next && duration) {
        setInterval(cycle, duration);
    }

});
