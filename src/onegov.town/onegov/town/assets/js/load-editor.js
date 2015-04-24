// run at the end of the markdown-editor js bundle
var inputs = document.getElementsByClassName('markdown');

for (var i=0; i<inputs.length; i++) {
    inputs[i].markdown_editor = new Editor({
        status: false,
        element: inputs[i]
    });    
    inputs[i].markdown_editor.render();
}
