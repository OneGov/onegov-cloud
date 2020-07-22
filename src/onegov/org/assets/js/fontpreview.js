$('#body_font_family_ui').children('option').each(function() {
    this.style.fontFamily = this.value.replace(';', '').replace(' !default', '');
});