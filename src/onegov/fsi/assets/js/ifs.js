function autoResize() {
    var newheight;
    var newwidth;
    var frame;

    for (frame of document.getElementsByClassName('resizeable')) {
        newheight = frame.contentWindow.document.body.scrollHeight;
        newwidth = frame.contentWindow.document.body.scrollWidth;
        frame.height = (newheight) + "px";
        frame.width = (newwidth) + "px";
    }

}
