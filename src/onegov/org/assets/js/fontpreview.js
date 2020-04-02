$('#font_family_sans_serif').children('option').each(function() {
    this.style.fontFamily = this.value.replace(';', '').replace(' !default', '');
});