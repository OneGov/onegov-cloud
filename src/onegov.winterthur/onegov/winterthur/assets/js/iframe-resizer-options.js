window.iFrameResizer = {
    heightCalculationMethod: function() {
        return $('.content').height() + $('header').height();
    },
    readyCallback: function() {
        parentIFrame.scrollTo(0, 0);
    }
};
