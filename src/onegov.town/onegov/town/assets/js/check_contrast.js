// check contrast of chose primary color
function hexToRgb(hex) {
    // see http://stackoverflow.com/a/5624139/3690178
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}


function luminance(r, g, b) {
    // see http://www.w3.org/TR/2008/REC-WCAG20-20081211/#relativeluminancedef
    // see http://stackoverflow.com/a/9733420/3690178
    var a = [r,g,b].map(function(v) {
        v /= 255;
        return (v <= 0.03928) ?
            v / 12.92 :
            Math.pow( ((v+0.055)/1.055), 2.4 );
        });
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}

var check_contrast = function() {
    // see http://www.w3.org/TR/2008/REC-WCAG20-20081211/#contrast-ratiodef
    // the theme lightens the primary color 30% for some elements
    var color = hexToRgb($(this).val());
    var ratio = (
        (luminance(255, 255, 255) + 0.05) /
        (luminance(color.r, color.g, color.b) / 0.7 + 0.05)
    );

    if ($(this).next('meter').length) {
        $(this).next('meter').val(ratio);
    } else {
        $(this).after('<meter min="1" max="21" low="4.5" value="' + ratio + '"></meter>');
    }
};
$('#primary_color').on('input propertychange paste', check_contrast);
$(document).ready(function (){
    check_contrast.apply($('#primary_color'));
});
