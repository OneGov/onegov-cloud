function autoResizebyID(id) {
    var newheight;
    var newwidth;

    if (document.getElementById) {
        newheight = document.getElementById(id).contentWindow.document.body.scrollHeight;
        newwidth = document.getElementById(id).contentWindow.document.body.scrollWidth;
    }

    document.getElementById(id).height = (newheight) + "px";
    document.getElementById(id).width = (newwidth) + "px";
}

function autoResize() {
    var newheight;
    var newwidth;
    var frame;
    if (document.getElementsByClassName) {
        for (frame of document.getElementsByClassName('resizeable')) {
            newheight = frame.contentWindow.document.body.scrollHeight;
            newwidth = frame.contentWindow.document.body.scrollWidth;
            frame.height = (newheight) + "px";
            frame.width = (newwidth) + "px";
        }
    }
}
