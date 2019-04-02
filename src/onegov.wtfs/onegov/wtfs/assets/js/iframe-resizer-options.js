window.iFrameResizer = {
    heightCalculationMethod: function() {
        return $('header').outerHeight(true) + $('main').height();
    },
    readyCallback: function() {
        parentIFrame.scrollTo(0, 0);
    }
};
