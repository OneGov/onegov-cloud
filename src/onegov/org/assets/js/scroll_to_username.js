// Scroll to the input username field
function elementInViewport(el) {
  var top = el.offsetTop;
  var left = el.offsetLeft;
  var width = el.offsetWidth;
  var height = el.offsetHeight;

  while(el.offsetParent) {
    el = el.offsetParent;
    top += el.offsetTop;
    left += el.offsetLeft;
  }

  return (
    top >= window.pageYOffset &&
    left >= window.pageXOffset &&
    (top + height) <= (window.pageYOffset + window.innerHeight) &&
    (left + width) <= (window.pageXOffset + window.innerWidth)
  );
}

$(document).ready(function () {
    var target = $('input#username')[0] || $('input#email')[0]
    if (target && !elementInViewport(target)) {
        $('html, body').animate({
            scrollTop: $(target).offset().top
        }, 'slow');
    }
});
