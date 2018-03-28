window.iFrameResizer = {
    heightCalculationMethod: function() {
        return $('.content').height();
    },
    readyCallback: function() {
        parentIFrame.scrollTo(0, 0);
    }
};
